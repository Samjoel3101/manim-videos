"""An experimental click-to-advance cut of the request-lifecycle film.

This is a SPIKE. It exists to answer one question: is a click-driven deck
(manim-slides) good enough to present this material, versus the continuous
45-second take the repo actually ships?

The design rule here is *subclass, never copy*. `TheLifecycle` already owns the
choreography; duplicating any of it would create a second copy of timings that
`videos/chatgpt_request_lifecycle/script.md` is the source of truth for. So this
scene inherits the shipped scene and only decides *where the clicks go*.

`Slide` comes first in the bases so its `construct`-time bookkeeping wraps the
render; the MRO is
`SlidesLifecycle -> Slide -> BaseSlide -> TheLifecycle -> MovingCameraScene -> Scene`,
i.e. a Slide IS a Scene and the shipped beat methods run unchanged.

Scope is the WHOLE FILM: all eleven beats, client through pull-back. The two
values the shipped `construct` threads between beats — the token strip from
`beat_tokenize` into `beat_prefill`, and the winning chip from `beat_sample`
into `beat_stream` — are threaded here the same way. Nothing else about the
choreography is touched.

Granularity: ONE CLICK PER ANIMATION
------------------------------------
An earlier cut stopped once per *beat*. That is a slideshow of long movies, not
a deck. This cut overrides `play` so that every animation the shipped
choreography runs gets its own stop — with no beat rewritten. Four things make
that work, and all four are load-bearing:

1. **`Scene.wait()` is `self.play(Wait(...))`** in manim 0.21. A naive split on
   every `play` therefore turns each per-character hold of
   `ChatInput.type_animation` into its own one-frame slide. Pure-`Wait` plays
   are filtered out: they neither open a slide nor disturb the merge flag, so
   the typing runs inside whatever slide is open and the deck's first stop rests
   on the fully typed question.

2. **A stop rests on the END of its animation**, because `next_slide()` closes
   the slide *before* the animation it precedes. That is the whole point: the
   click lands on the filled checklist, the grown meter, the completed legend —
   never on a fade in progress.

3. **Clear-downs merge FORWARD** (see `_is_clear_down`). Every shipped beat
   clears its own props before the camera leaves. On its own, such a play makes
   a stop whose entire content is "the text you were reading disappears", ending
   on an empty bay. So the split is taken *before* the clear-down (it opens a
   new slide) and *suppressed* before the play that follows it, giving one click
   that reads "old props clear, camera moves on, new content appears" and rests
   on the new content. Getting this backwards — suppressing before the
   clear-down — merges it into the *previous* slide instead, so content would
   appear and immediately vanish under one click. Direction is everything here.

4. **Some repeats must not become clicks** (see `no_stops`). The back half of
   the film repeats structures whose *shape* is the content rather than a
   sequence of states to step through; the decode ramp at the end is ten token
   cycles of twenty plays, accelerating, and twenty clicks through it destroys
   the one thing it exists to show. Those regions play through under a single
   click. See `_token_cycle` below for exactly which, and why the loops that
   are NOT suppressed (the orchestrator's context bar, the decode bay's pulses,
   the four countable token cycles) were left alone.

There is deliberately no settling `wait` before a stop, and no longer one at the
end either. Commit 714204e added a per-stop `SETTLE`, which was the right fix
for beat-level stops and is exactly wrong here: a trailing wait is a pure-`Wait`
play, so it extends the slide past the end of the animation and parks the stop
on the cleared state — the disappearing-text complaint, reintroduced. The
top-band cut then kept one `END_HOLD` at the very end, because that cut's last
play was a clear-down with no successor to merge into and no next slide to carry
the frame. The full film does not need it: `beat_pull_back` ends with
`self.play(FadeOut(caption))` followed by the shipped `self.wait(0.5)`, and that
wait is a pure-`Wait` play, so it already extends the final slide past the fade
and rests it on the emptied plant. `END_HOLD` is gone rather than kept with a
stale comment; the film supplies its own hold.
"""

from __future__ import annotations

import pathlib
import sys
from contextlib import contextmanager
from typing import Iterable, Iterator

from manim import (
    Animation,
    Create,
    DrawBorderThenFill,
    FadeIn,
    FadeOut,
    Flash,
    LaggedStart,
    MoveAlongPath,
    Uncreate,
    Wait,
)
from manim_slides import Slide

# The shipped scene lives under `videos/<slug>/scenes/` and imports its set as a
# sibling top-level module, so that directory goes on the path rather than being
# imported as a package.
_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SCENES = _ROOT / "videos" / "chatgpt_request_lifecycle" / "scenes"
for _p in (str(_ROOT), str(_SCENES)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib import camera, theme  # noqa: E402
from lib.components.chat_ui import TypingIndicator  # noqa: E402
from lifecycle_set import LifecycleSet  # noqa: E402
from scene_lifecycle import W_CHAT, TheLifecycle  # noqa: E402

#: Animation classes that put something ON the screen. A clear-down is defined
#: as "props leaving, nothing arriving", and the first cut of that predicate
#: tested only `FadeIn` — which is not the same claim. `beat_sample` plays
#: `Flash(kv) + FadeOut(kv)` (`scene_lifecycle.py:843-848`): the chip's keys and
#: values being absorbed into the cache, with the flash carrying the arrival.
#: Under a FadeIn-only test that play reads as a clear-down and merges forward
#: into `:849`, which is a real clear-down — so the merged stop would rest on a
#: cleared bay, the exact failure this whole design exists to prevent.
#:
#: `MoveAlongPath` is here for the same reason: a dot travelling a rail is the
#: content of the play it is in, whatever else fades out alongside it.
#:
#: Known limitation, stated rather than papered over: content introduced by
#: `.animate.set_opacity(1.0)` is still invisible to this test, because a
#: `_MethodAnimation` does not advertise its direction. No play in this film
#: combines a bare opacity-raise with a `FadeOut` and nothing else, but a new
#: beat that did would be misclassified.
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
#: `.animate` as one — including `camera.focus`, which returns a built
#: frame animation. A first cut of this file did exactly that, and the effect
#: was invisible in the counts: it reinstated the "a camera move disqualifies a
#: clear-down" rule the docstring below says it removes, and the deck rendered
#: to the same 72 stops either way. What gave it away was the resting frame of
#: `scene_lifecycle.py:849` still carrying a half-faded caption.
#:
#: The beats also pass `.animate` builders UNBUILT (`_AnimationBuilder` is not
#: an `Animation` at all), so a class test cannot see those either way. The
#: honest statement of the rule is therefore: arrival means one of the
#: `INTRODUCING` classes; a `.animate` call is never counted as an arrival,
#: which is right for the glow resets, the meters and the camera, and wrong for
#: a bare `.animate.set_opacity(1.0)` — no play in this film pairs one of those
#: with a `FadeOut` and nothing else, but a new beat that did would be
#: misclassified.


class SlidesLifecycle(Slide, TheLifecycle):
    """The whole film, cut into one click-advanced slide per animation."""

    #: Which animation gets the deck's single looping stop, counting non-wait
    #: plays from 1. Animation 3 is the `LaggedStart` that brings up the three
    #: dots of the typing indicator: a stop that reads as a live idle, and the
    #: only animation in the film whose replay is honest rather than a value
    #: snapping back to its start — the back half's candidates (a token lapping
    #: the decode loop, a packet flying home) all end somewhere other than where
    #: they began, so looping them teleports the dot. Every other stop freezes
    #: on its last frame, so a viewer can compare a frozen hold with an animated
    #: one in a single sitting — which is the thing this spike asks them to
    #: judge. The index is checked against the animation itself at the split
    #: site (`_is_loop_target`), not just against the totals below.
    LOOP_ON_ANIMATION = 3

    #: Tripwire, not a gate. The counts below are what the shipped choreography
    #: produces today. If a beat gains or loses an animation these stop matching
    #: — the render prints a warning rather than failing, because this is a
    #: spike and a stale constant must not block a render of the real film.
    EXPECTED_ANIMATIONS = 97
    EXPECTED_STOPS = 70

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        #: Non-wait plays seen so far.
        self._anim_n = 0
        #: Has anything at all been played, INCLUDING pure waits? The film
        #: opens with `type_animation`, which is nothing but waits, so this is
        #: what lets the typing close its own slide — resting on the fully
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
        #: `_token_cycle` — see `_token_cycle`.
        self._sticky = False
        #: Are we inside a `_token_cycle` call right now?
        self._in_token_cycle = False
        #: Regions suppressed, for the report the render prints.
        self._regions = 0

    # ------------------------------------------------------------- suppression
    @contextmanager
    def no_stops(self):
        """Animations inside play as ONE click.

        For repeat structures whose shape IS the content — the decode ramp's
        acceleration above all. The first play inside still opens a stop (so the
        region is its own click rather than an extension of the previous one);
        every play after it is merged into that same slide.

        `_prev_was_clear_down` is deliberately NOT saved and restored: it must
        keep tracking through the region so that the boundary behaves like any
        other. If the last play inside the region is a clear-down, the first
        play after it merges forward into the region exactly as it would
        anywhere else in the film.
        """
        prev = (self._suppress, self._region_first, self._sticky)
        self._suppress, self._region_first, self._sticky = True, True, False
        self._regions += 1
        try:
            yield
        finally:
            self._suppress, self._region_first, self._sticky = prev

    def _begin_sticky(self) -> None:
        """Open a suppressed region that no `with` block will close.

        The decode ramp is six consecutive `_token_cycle` calls in the MIDDLE of
        `beat_pull_back`, and this scene may not edit that beat — so there is no
        block to wrap. Instead the first ramp cycle opens the region and `play`
        closes it again at the first animation that does not come from inside a
        cycle (the caption's final fade-out). That keeps the whole ramp on one
        click without the scene needing to know how many cycles there are.
        """
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

    def _token_cycle(self, cycle, home, lap: float, emit: float, *,
                     comet: bool) -> None:
        """One decode step, as ONE click — and the whole fast ramp as one more.

        The shipped cycle is two plays: lap the loop inside the box, then fly a
        token home and reveal one word. Split per play, the first of the two
        rests on a dot back where it started with no new word — a click that
        shows nothing. So each cycle is atomic.

        The two groups are then treated differently, by the rule "keep stops
        unless the repetition is a ramp or a texture rather than a sequence of
        distinct states":

        * `CYCLES_EXPLICIT` (the four the film's own comment says the viewer is
          meant to COUNT) are a sequence of distinct states — one more word in
          the bubble each time — so they keep one click each. They are the
          `comet=True` calls.
        * `CYCLES_FAST` is a halving ramp, and `scene_lifecycle.py:139-147` says
          its shape IS the acceleration and that flattening it removes the one
          thing that reads as a machine speeding up. Six clicks would flatten it
          exactly as surely as re-timing it would; twenty (per play) worse. The
          whole ramp is ONE click. They are the `comet=False` calls — the film
          drops the comet below `EMIT_RUN_TIME` precisely because these are the
          fast ones, so the flag is the group, not a proxy for it.
        """
        if comet:
            with self.no_stops():
                super()._token_cycle(cycle, home, lap, emit, comet=comet)
            return
        self._begin_sticky()
        self._in_token_cycle = True
        try:
            super()._token_cycle(cycle, home, lap, emit, comet=comet)
        finally:
            self._in_token_cycle = False

    # ------------------------------------------------------------------ split
    @staticmethod
    def _flatten(args: Iterable) -> list:
        """`self.play(*anims)` and `self.play([a, b])` both occur in the beats."""
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
        `FadeOut`" either: the real tails pair their fades with a
        glow dimming back to its resting stroke (`:322-328` edge, `:377-382`
        gateway) and with the packet dropping to the next rail (orchestrator),
        and a predicate that strict would match none of them.

        A clear-down is: at least one `FadeOut` and nothing being INTRODUCED
        (see `INTRODUCING` — arrival is not only `FadeIn`).

        **A camera move does not disqualify one, and that is a correction.**
        The top-band cut also required the camera to stay put, on the reasoning
        that "the camera carries on while the old props go" is a transition
        rather than a clear-down. It is not a distinction the frames support: a
        travelling clear-down ends on the same half-faded prop as a stationary
        one, because Manim renders an animation's last frame at
        `t = run_time - 1/fps` and `FadeOut` only removes the mobject after
        that. `scene_lifecycle.py:849-856` is the case that proved it — the
        sampler beat fades its loop caption out while the camera swings back to
        the bay, and at 480p15 the resting frame carried a clearly legible ghost
        of both caption lines. Merging it forward gives the same one click the
        rule gives everywhere else: props go, camera travels, next content
        arrives, and the stop rests on the content.

        No play in the top band combines a `FadeOut` with a camera move, so the
        27 stops the user signed off on are untouched by this; the two plays it
        changes are `:849` (above) and `:984`, where the spinner fades out as
        the camera returns to the chat — that one now rests on the bubble with
        its first word in it instead of on an empty bubble frame.

        `:940-956` of the stream beat is still not a clear-down, and no longer
        because of the camera: four packets fly home in it, and `MoveAlongPath`
        is an arrival.
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
        """Is this play the typing-indicator's dots, i.e. what the loop claims?

        `LOOP_ON_ANIMATION` is an index, and an index is only as good as the
        ordering behind it. The totals tripwire is a proxy — a reorder that
        preserves the counts moves the loop silently — so the thing the index
        names is checked directly: one `LaggedStart` whose members all animate
        dots belonging to a `TypingIndicator` currently on screen.
        """
        flat = self._flatten(args)
        if len(flat) != 1 or not isinstance(flat[0], LaggedStart):
            return False
        dots = set()
        for mob in self.mobjects:
            for sub in mob.get_family():
                if isinstance(sub, TypingIndicator):
                    dots.update(id(d) for d in sub.dots)
        if not dots:
            return False
        members = [a for a in self._walk(flat) if a is not flat[0]]
        return bool(members) and all(
            id(getattr(a, "mobject", None)) in dots for a in members
        )

    def play(self, *args: Animation, **kwargs):  # type: ignore[override]
        if self._in_split:
            return super().play(*args, **kwargs)
        if self._is_pure_wait(args):
            self._played_anything = True
            return super().play(*args, **kwargs)

        # The decode ramp's region has no closing `with`: it ends at the first
        # animation that is not part of a token cycle.
        if self._sticky and not self._in_token_cycle:
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
                    f"{self.LOOP_ON_ANIMATION} is no longer the typing-indicator"
                    " dots — LOOP_ON_ANIMATION points at the wrong animation",
                    flush=True,
                )
            self._in_split = True
            try:
                self.next_slide(loop=loop)
            finally:
                self._in_split = False
            self._stops += 1

        self._played_anything = True
        return super().play(*args, **kwargs)

    # -------------------------------------------------------------- construct
    def construct(self) -> None:
        # Mirrors `TheLifecycle.construct` exactly — prelude, all eleven beats,
        # and the two values threaded between them. The beats depend on
        # `self.set` and `self.parcel` existing, and on the camera starting
        # snapped to the chat window at W_CHAT.
        theme.apply(self)

        self.set = LifecycleSet()
        self.add(self.set)
        camera.snap_to(self, self.set.chat, width=W_CHAT)

        self.parcel: list = []

        self.beat_client()
        self.beat_edge()
        self.beat_gateway()
        self.beat_orchestrator()
        strip = self.beat_tokenize()
        self.beat_prefill(strip)
        self.beat_decode()
        token = self.beat_sample()
        self.beat_stream(token)
        self.beat_after()
        self.beat_pull_back()

        print(
            f"\n### slides: {self._anim_n} animations -> {self._stops} stops"
            f" ({self._regions} suppressed regions,"
            f" loop on animation {self.LOOP_ON_ANIMATION})",
            flush=True,
        )
        if (self._anim_n, self._stops) != (
            self.EXPECTED_ANIMATIONS,
            self.EXPECTED_STOPS,
        ):
            print(
                "### WARNING: expected "
                f"{self.EXPECTED_ANIMATIONS} animations / {self.EXPECTED_STOPS}"
                " stops — the choreography changed, re-check LOOP_ON_ANIMATION",
                flush=True,
            )
