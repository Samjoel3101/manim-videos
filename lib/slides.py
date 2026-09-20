"""Turn a shipped continuous-shot scene into a click-advanced deck.

The house format is one uncut camera move (see `AGENTS.md` → "Continuous
shots"). A deck is the *same film*, cut at every animation so a presenter can
step through it. Both outputs come from one choreography: a deck **subclasses**
its film's scene and decides only *where the clicks go*. It copies no timings,
so `videos/<slug>/script.md` stays the single source of truth for pacing.

Usage, in `videos/<slug>/slides.py`::

    class SlidesFoo(ClickDeck, Slide, TheFoo):
        EXPECTED_ANIMATIONS = 61
        EXPECTED_STOPS = 40

That is the whole file for a film with no ramps. `ClickDeck.construct` calls
`super().construct()` — i.e. the shipped one, unchanged — and then prints the
split report, so a deck needs no `construct` of its own.

Base order matters. `ClickDeck` first so its `play` override wraps everything;
`Slide` next so manim-slides' `construct`-time bookkeeping wraps the render;
the film's scene last. The MRO is
`SlidesFoo -> ClickDeck -> Slide -> BaseSlide -> TheFoo -> MovingCameraScene -> Scene`,
i.e. a deck IS a Scene and the shipped beat methods run unchanged.

This module deliberately does **not** import `manim_slides`: it is a plain
mixin over `Scene`, so `lib/` stays importable without the deck dependency and
the Evaluator's `import` gate does not pull in a presentation library. The
`Slide` base is supplied by the per-video deck.

Granularity: ONE CLICK PER ANIMATION
------------------------------------
Stopping once per *beat* is a slideshow of long movies, not a deck. `play` is
overridden instead, so every animation the shipped choreography runs gets its
own stop — with no beat rewritten. Four behaviours make that work, and all four
are load-bearing. They were each paid for by looking at rendered frames; see
`docs/slides.md` for the full account.

1. **`Scene.wait()` is `self.play(Wait(...))`** in manim 0.21. A naive split on
   every `play` therefore turns each per-character hold of a typing animation
   into its own one-frame slide — the first probe of this produced 57 stops, 29
   of them a single frame. Pure-`Wait` plays are filtered out: they neither open
   a slide nor disturb the merge flag, so typing runs inside whatever slide is
   open, and a narration hold **extends the open slide** instead of costing a
   click.

2. **A stop rests on the END of its animation**, because `next_slide()` closes
   the slide *before* the animation it precedes. That is the whole point: the
   click lands on the filled checklist, the grown meter, the completed legend —
   never on a fade in progress.

3. **Clear-downs merge FORWARD** (see `_is_clear_down`). Every beat clears its
   own props before the camera leaves — a house rule, and the reason this merge
   is possible at all. On its own, such a play makes a stop whose entire content
   is "the text you were reading disappears", ending on an empty bay. So the
   split is taken *before* the clear-down (it opens a new slide) and
   *suppressed* before the play that follows it, giving one click that reads
   "old props clear, camera moves on, new content appears" and rests on the new
   content. Getting this backwards — suppressing before the clear-down — merges
   it into the *previous* slide instead, so content would appear and instantly
   vanish under one click. Direction is everything here.

4. **Some repeats must not become clicks** (see `no_stops`). A ramp whose
   *shape* is the content — a loop accelerating over six passes — is destroyed
   by stepping through it. Those regions play through under a single click. The
   rule applied throughout: keep the stops unless the repetition is a ramp or a
   texture rather than a sequence of distinct states.

There is deliberately no settling `wait` before a stop, and none at the end
either. A trailing wait is a pure-`Wait` play, so it extends the slide past the
end of the animation and parks the stop on the cleared state — the
disappearing-text failure, reintroduced. A film that ends with its own trailing
`self.wait(t)` after the final fade needs no end hold; merging clear-downs
forward removes the need everywhere else.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable, Iterator

from manim import (
    Animation,
    Create,
    DrawBorderThenFill,
    FadeIn,
    FadeOut,
    Flash,
    MoveAlongPath,
    Uncreate,
    Wait,
)

#: Animation classes that put something ON the screen. A clear-down is "props
#: leaving, nothing arriving", and the first cut of that predicate tested only
#: `FadeIn` — which is not the same claim. A beat that absorbs a chip into a
#: cache with `Flash(kv) + FadeOut(kv)` reads as a clear-down under a
#: FadeIn-only test, and then merges forward into the *genuine* clear-down after
#: it, so the stop rests on a cleared bay — the exact failure this design exists
#: to prevent.
#:
#: `MoveAlongPath` is here for the same reason: a dot travelling a rail is the
#: content of the play it is in, whatever else fades out alongside it.
#:
#: Known limitation, stated rather than papered over: content introduced by
#: `.animate.set_opacity(1.0)` is invisible to this test, because a
#: `_MethodAnimation` does not advertise its direction. See `docs/slides.md`
#: → "Authoring rules"; `videos/chatgpt_message_journey` has one such play and
#: it is documented there rather than worked around here.
INTRODUCING = (
    FadeIn,
    Flash,
    Create,
    DrawBorderThenFill,
    MoveAlongPath,
)

#: Subclasses of the above that do the OPPOSITE and must not be read as
#: arrivals — `Uncreate` is a `Create`.
NOT_INTRODUCING = (FadeOut, Uncreate)

#: Deliberately NOT in `INTRODUCING`, and this was measured rather than
#: assumed: `Transform`. Every `.animate` resolves to `_MethodAnimation`, whose
#: MRO is `MoveToTarget -> Transform` and does NOT pass through `ApplyMethod`,
#: so listing `Transform` as an arrival silently classifies every built
#: `.animate` as one — including `camera.focus`, which returns a built frame
#: animation. A first cut of this machinery did exactly that, and the effect was
#: invisible in the counts: it reinstated the "a camera move disqualifies a
#: clear-down" rule `_is_clear_down` says it removes, and the deck rendered to
#: the same stop count either way. What gave it away was the resting frame of
#: one play still carrying a half-faded caption.
#:
#: Beats also pass `.animate` builders UNBUILT (`_AnimationBuilder` is not an
#: `Animation` at all), so a class test cannot see those either way. The honest
#: statement of the rule is therefore: arrival means one of the `INTRODUCING`
#: classes, and a `.animate` call is never counted as an arrival — right for
#: glow resets, meters and the camera, wrong for a bare
#: `.animate.set_opacity(1.0)`.


class ClickDeck:
    """Split a shipped scene into one click-advanced slide per animation.

    Mix in FIRST, before `manim_slides.Slide` and the film's own scene.
    """

    #: Which animation gets a looping stop, counting non-wait plays from 1, or
    #: `None` for a deck where every stop freezes. A loop is honest only for an
    #: animation that ends where it began — a live idle such as typing dots. An
    #: animation that ends somewhere else (a token lapping a loop, a packet
    #: flying home) teleports its mobject on replay.
    LOOP_ON_ANIMATION: int | None = None

    #: Tripwire, not a gate. What the shipped choreography produces today. If a
    #: beat gains or loses an animation these stop matching and the render
    #: prints a warning — it does not fail, because a stale constant must never
    #: block a render of the real film. `tests/test_slides_convention.py` is
    #: where the numbers are actually enforced.
    EXPECTED_ANIMATIONS: int | None = None
    EXPECTED_STOPS: int | None = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        #: Non-wait plays seen so far.
        self._anim_n = 0
        #: Has anything at all been played, INCLUDING pure waits? A film that
        #: opens with a typing animation opens with nothing but waits, so this
        #: is what lets the typing close its own slide — resting on the fully
        #: typed question — before the first real animation opens the next.
        self._played_anything = False
        #: Re-entry guard, in case `next_slide()` ever plays something itself.
        self._in_split = False
        #: Was the previous non-wait play a clear-down? Pure-`Wait` plays must
        #: NOT touch this: a hold between a clear-down and the next beat would
        #: otherwise break the merge.
        self._prev_was_clear_down = False
        #: Slides opened, counting the one that is open before the first play.
        self._stops = 1
        #: Splitting suppressed? Set by `no_stops`.
        self._suppress = False
        #: The FIRST play of a suppressed region still splits normally, so the
        #: region opens its own stop instead of being glued onto the one before
        #: it. Only the plays after it are swallowed.
        self._region_first = False
        #: A suppressed region that closes itself at the first play from outside
        #: the repeated unit — see `sticky_stops`.
        self._sticky = False
        #: Are we inside one repetition of a sticky region right now?
        self._inside_sticky_unit = False
        #: Regions suppressed, for the report the render prints.
        self._regions = 0
        #: Nominal `run_time` accumulated into the slide that is currently open.
        #: Only the probe reads this; it costs one float per play.
        self._chunk_time = 0.0
        #: Nominal seconds per stop, in order, closed as each slide closes.
        self.chunk_times: list[float] = []

    # ------------------------------------------------------------- suppression
    @contextmanager
    def no_stops(self):
        """Animations inside play as ONE click.

        For repeat structures whose shape IS the content — an accelerating ramp
        above all. The first play inside still opens a stop (so the region is
        its own click rather than an extension of the previous one); every play
        after it is merged into that same slide.

        `_prev_was_clear_down` is deliberately NOT saved and restored: it must
        keep tracking through the region so the boundary behaves like any other.
        If the last play inside the region is a clear-down, the first play after
        it merges forward into the region exactly as it would anywhere else.
        """
        prev = (self._suppress, self._region_first, self._sticky)
        self._suppress, self._region_first, self._sticky = True, True, False
        self._regions += 1
        try:
            yield
        finally:
            self._suppress, self._region_first, self._sticky = prev

    @contextmanager
    def sticky_stops(self):
        """One repetition of a region that spans N consecutive calls.

        A ramp is often N consecutive calls to a helper in the MIDDLE of a beat
        the deck may not edit, so there is no block to wrap with `no_stops`.
        Wrapping each repetition in `sticky_stops` instead opens the region on
        the first one and leaves it open; `play` closes it again at the first
        animation that does not come from inside a repetition. That keeps the
        whole ramp on one click without the deck needing to know how many
        repetitions there are.
        """
        self._open_sticky()
        prev = self._inside_sticky_unit
        self._inside_sticky_unit = True
        try:
            yield
        finally:
            self._inside_sticky_unit = prev

    def _open_sticky(self) -> None:
        if self._sticky:
            return
        self._suppress = True
        self._region_first = True
        self._sticky = True
        self._regions += 1

    def _end_sticky(self) -> None:
        self._suppress = False
        self._region_first = False
        self._sticky = False

    def _sticky_play(self, args) -> bool:
        """Is this play one repetition of a region that should be one click?

        The predicate form of `sticky_stops`, for a ramp or texture that is
        written *inline in a beat the deck may not edit* — there is no call to
        wrap, so the plays are recognised instead. The region opens at the first
        play that matches and closes at the first one that does not, so the
        whole run is a single click.

        Returning a constant `False` (the default) means a deck opts out
        entirely. Recognise plays by what they animate, not by their index: an
        index moves silently when a beat is re-ordered.
        """
        return False

    # ------------------------------------------------------------------ split
    @staticmethod
    def _flatten(args: Iterable) -> list:
        """`self.play(*anims)` and `self.play([a, b])` both occur in beats."""
        flat: list = []
        for arg in args:
            if isinstance(arg, (list, tuple)):
                flat.extend(arg)
            else:
                flat.append(arg)
        return flat

    @classmethod
    def _walk(cls, anims: Iterable) -> Iterator:
        """Yield each animation and, recursively, the members of any group."""
        for anim in anims:
            yield anim
            sub = getattr(anim, "animations", None)
            if sub:
                yield from cls._walk(sub)

    @classmethod
    def _is_pure_wait(cls, args) -> bool:
        flat = cls._flatten(args)
        return bool(flat) and all(isinstance(a, Wait) for a in flat)

    def _is_clear_down(self, args) -> bool:
        """Is this play a beat's clear-down — props leaving, nothing arriving?

        Not simply "contains a `FadeOut`", and not "every animation is a
        `FadeOut`" either: real tails pair their fades with a glow dimming back
        to its resting stroke and with a packet dropping to the next rail, and a
        predicate that strict would match none of them.

        A clear-down is: **at least one `FadeOut` and nothing being INTRODUCED**
        (see `INTRODUCING` — arrival is not only `FadeIn`).

        **A camera move does not disqualify one, and that is a correction.** An
        earlier cut also required the camera to stay put, on the reasoning that
        "the camera carries on while the old props go" is a transition rather
        than a clear-down. The frames do not support the distinction: a
        travelling clear-down ends on the same half-faded prop as a stationary
        one, because Manim renders an animation's last frame at
        `t = run_time - 1/fps` and `FadeOut` only removes the mobject after
        that. The case that proved it was a caption fading while the camera
        swung back to a bay — at 480p15 the resting frame carried a clearly
        legible ghost of both caption lines. Merging it forward gives the same
        one click the rule gives everywhere else: props go, camera travels, next
        content arrives, and the stop rests on the content.
        """
        flat = list(self._walk(self._flatten(args)))
        if not any(isinstance(a, FadeOut) for a in flat):
            return False
        for anim in flat:
            if isinstance(anim, INTRODUCING) and not isinstance(
                anim, NOT_INTRODUCING
            ):
                return False
        return True

    def _is_loop_target(self, args) -> bool:
        """Is this play the one `LOOP_ON_ANIMATION` claims it is?

        An index is only as good as the ordering behind it, and the totals
        tripwire is a proxy — a reorder that preserves the counts moves the loop
        silently. A deck that sets `LOOP_ON_ANIMATION` should override this to
        check the animation itself at the split site. The default accepts
        anything, so a deck with no loop costs nothing.
        """
        return True

    def play(self, *args: Animation, **kwargs):  # type: ignore[override]
        if self._in_split:
            return self._play_through(*args, **kwargs)
        if self._is_pure_wait(args):
            # A hold extends the slide that is already open. It must not touch
            # `_prev_was_clear_down`, or a hold between a clear-down and the
            # next beat would break the merge.
            self._played_anything = True
            return self._play_through(*args, **kwargs)

        # A sticky region has no closing `with`: it ends at the first animation
        # that is not part of one of its repetitions. A repetition is either
        # wrapped (`sticky_stops`) or recognised (`_sticky_play`).
        sticky_unit = self._inside_sticky_unit or self._sticky_play(args)
        if sticky_unit and not self._suppress:
            self._open_sticky()
        elif self._sticky and not sticky_unit:
            self._end_sticky()

        self._anim_n += 1
        merge_forward = self._prev_was_clear_down
        self._prev_was_clear_down = self._is_clear_down(args)

        suppressed = self._suppress and not self._region_first
        self._region_first = False

        # `next_slide()` ENDS the open slide and BEGINS a new one, so the
        # animation below lands in the NEW slide. Suppressing the call here is
        # therefore what merges this animation with the clear-down before it.
        if self._played_anything and not merge_forward and not suppressed:
            loop = self._anim_n == self.LOOP_ON_ANIMATION
            if loop and not self._is_loop_target(args):
                print(
                    "### WARNING: animation "
                    f"{self.LOOP_ON_ANIMATION} is not the animation"
                    " LOOP_ON_ANIMATION names — the choreography was reordered",
                    flush=True,
                )
            self._in_split = True
            try:
                self.next_slide(loop=loop)
            finally:
                self._in_split = False
            self._stops += 1
            self.chunk_times.append(self._chunk_time)
            self._chunk_time = 0.0

        self._played_anything = True
        return self._play_through(*args, **kwargs)

    def _play_through(self, *args, **kwargs):
        """Hand the play to the renderer.

        Split out so a no-render probe can replace the *rendering* without
        touching the splitting above — which is what keeps
        `tests/test_slides_convention.py` inside the fast `unit` gate.
        """
        return super().play(*args, **kwargs)  # type: ignore[misc]

    # -------------------------------------------------------------- construct
    def construct(self) -> None:
        """Run the shipped film, then report the split.

        `super().construct()` is the film's own `construct`, unchanged — which
        is why a per-video deck needs no `construct` of its own and cannot drift
        from the film's beat order.
        """
        super().construct()  # type: ignore[misc]
        self.close_last_chunk()
        print(self.split_report(), flush=True)
        if self.EXPECTED_ANIMATIONS is not None and (
            self._anim_n,
            self._stops,
        ) != (self.EXPECTED_ANIMATIONS, self.EXPECTED_STOPS):
            print(
                "### WARNING: expected "
                f"{self.EXPECTED_ANIMATIONS} animations / {self.EXPECTED_STOPS}"
                " stops — the choreography changed, re-check LOOP_ON_ANIMATION",
                flush=True,
            )

    def close_last_chunk(self) -> None:
        """Close the slide that is open when the film ends. Idempotent."""
        if len(self.chunk_times) < self._stops:
            self.chunk_times.append(self._chunk_time)
            self._chunk_time = 0.0

    def split_report(self) -> str:
        return (
            f"\n### slides: {self._anim_n} animations -> {self._stops} stops"
            f" ({self._regions} suppressed regions,"
            f" loop on animation {self.LOOP_ON_ANIMATION})"
        )


# --------------------------------------------------------------------- probe
class DeckStats:
    """What one no-render pass of a deck's `construct` measured."""

    def __init__(self, animations: int, stops: int, regions: int,
                 chunk_times: list[float]) -> None:
        self.animations = animations
        self.stops = stops
        self.regions = regions
        self.chunk_times = chunk_times

    @property
    def total_time(self) -> float:
        return sum(self.chunk_times)

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        return (
            f"DeckStats(animations={self.animations}, stops={self.stops}, "
            f"regions={self.regions}, total_time={self.total_time:.6f})"
        )


class _NoRenderPlay:
    """Advance animations to their final state without rendering a frame.

    Mixed in FIRST, so its `_play_through` wins over `ClickDeck._play_through`
    and its `next_slide` over manim-slides'. Everything else — mobject
    construction, the beats, and the whole split state machine — runs exactly as
    it does under a real render, which is what makes the probe a check of the
    split rather than a re-implementation of it.

    Rendering a 60-second film at 480p15 takes minutes; this takes seconds, so
    the convention test can live in the `unit` gate.
    """

    #: Class-level default so a plain (non-deck) scene can be probed too.
    _chunk_time = 0.0

    def next_slide(self, *args, **kwargs) -> None:  # type: ignore[override]
        return None

    def _play_through(self, *args, **kwargs):
        kwargs.pop("subcaption", None)
        kwargs.pop("subcaption_duration", None)
        kwargs.pop("subcaption_offset", None)
        anims = self.compile_animations(*args, **kwargs)  # type: ignore[attr-defined]
        self.add_mobjects_from_animations(anims)  # type: ignore[attr-defined]
        duration = self.get_run_time(anims)  # type: ignore[attr-defined]
        for anim in anims:
            anim._setup_scene(self)
            anim.begin()
            # `finish()` interpolates to alpha 1, so the mobjects end where a
            # real render would leave them and later layout code sees the same
            # geometry.
            anim.finish()
            anim.clean_up_from_scene(self)
        self._chunk_time += duration  # type: ignore[attr-defined]
        return None


class _NoRenderScene(_NoRenderPlay):
    """`_NoRenderPlay` for a scene that is NOT a deck.

    A plain scene calls `Scene.play` directly, with no `ClickDeck` in the MRO to
    route it through `_play_through`, so `play` itself is the seam here. Kept
    separate precisely because overriding `play` in `_NoRenderPlay` would
    shadow `ClickDeck.play` and silently disable the splitting the probe exists
    to measure.
    """

    def play(self, *args, **kwargs):  # type: ignore[override]
        return self._play_through(*args, **kwargs)


def film_time(scene_cls: type) -> float:
    """Nominal seconds the shipped scene plays, with nothing rendered.

    The figure to compare a deck's total against: a deck that splits correctly
    adds and loses no time, because it runs the same plays.
    """
    probe_cls = type(f"Probe{scene_cls.__name__}", (_NoRenderScene, scene_cls), {})
    scene = probe_cls()
    scene.construct()
    return scene._chunk_time


def probe(deck_cls: type) -> DeckStats:
    """Run `deck_cls.construct()` with no rendering and report the split."""
    probe_cls = type(f"Probe{deck_cls.__name__}", (_NoRenderPlay, deck_cls), {})
    scene = probe_cls()
    scene.construct()
    scene.close_last_chunk()
    return DeckStats(
        animations=scene._anim_n,
        stops=scene._stops,
        regions=scene._regions,
        chunk_times=list(scene.chunk_times),
    )
