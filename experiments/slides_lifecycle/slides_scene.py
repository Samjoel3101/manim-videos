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

Scope is the top band only — client, edge, gateway, orchestrator: the film's
first ~18 seconds. The tokenizer and decode beats are deliberately excluded;
`beat_tokenize` hands a token strip to `beat_prefill` and the decode loop's
timing constants are load-bearing, so chopping clicks into them would change
the film rather than present it.

Granularity: ONE CLICK PER ANIMATION
------------------------------------
An earlier cut stopped once per *beat* (four stops). That is a slideshow of
four long movies, not a deck. This cut overrides `play` so that every animation
the shipped choreography runs gets its own stop — with no beat rewritten. Three
things make that work, and all three are load-bearing:

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

There is deliberately no settling `wait` before a stop. Commit 714204e added
one, which was the right fix for beat-level stops and is exactly wrong here: a
trailing wait is a pure-`Wait` play, so it extends the slide past the end of the
animation and parks the stop on the cleared state — the disappearing-text
complaint, reintroduced. Merging clear-downs forward removes the need for it.
The one exception is a single hold at the very END of the deck (`END_HOLD`),
where the last clear-down has no successor to merge into and no next slide to
carry the frame; without it the deck's final still is a half-faded caption.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Iterable, Iterator

from manim import Animation, FadeIn, FadeOut, Wait
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
from lifecycle_set import LifecycleSet  # noqa: E402
from scene_lifecycle import W_CHAT, TheLifecycle  # noqa: E402


class SlidesLifecycle(Slide, TheLifecycle):
    """The top band of the film, cut into one click-advanced slide per animation."""

    #: Which animation gets the deck's single looping stop, counting non-wait
    #: plays from 1. Animation 3 is the `LaggedStart` that brings up the three
    #: dots of the typing indicator: a stop that reads as a live idle, and the
    #: only animation in the top band whose replay is honest rather than a
    #: value snapping back to its start. Every other stop freezes on its last
    #: frame, so a viewer can compare a frozen hold with an animated one in a
    #: single sitting — which is the thing this spike asks them to judge.
    LOOP_ON_ANIMATION = 3

    #: A hold at the very END of the deck, and nowhere else. The top band's
    #: last animation is a clear-down with nothing after it to merge into, and
    #: manim renders an animation's final frame at `t = run_time - 1/fps`, so
    #: the final chunk would otherwise be cut while the fading props are still
    #: faintly drawn — verified: the 480p15 chunk ended on a half-transparent
    #: caption. `FadeOut` has already removed the mobjects by then, so a few
    #: still frames after the last play rest on the emptied band. This is NOT
    #: the per-stop `SETTLE` wait that 714204e added and this cut removed: that
    #: one sat before EVERY stop and, being a pure-`Wait` play, extended each
    #: slide past its animation and parked it on the cleared state. One hold
    #: after the last click is the opposite — there is no next slide to carry
    #: the frame.
    END_HOLD = 0.35

    #: Tripwire, not a gate. The counts below are what the shipped choreography
    #: produces today (28 non-wait plays, 2 of them merged forward into their
    #: successors, hence 27 stops). If a beat gains or loses an animation these
    #: stop matching and `LOOP_ON_ANIMATION` is probably pointing at the wrong
    #: thing — the render prints a warning rather than failing, because this is
    #: a spike and a stale constant must not block a render of the real film.
    EXPECTED_ANIMATIONS = 28
    EXPECTED_STOPS = 27

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

        Not simply "contains a `FadeOut`". The beats combine a `FadeOut` with a
        `camera.focus` move in one `self.play` (the camera carries on while the
        old props go), and those are transitions, not clear-downs. Nor is it
        "every animation is a `FadeOut`": the real tails pair their fades with a
        glow dimming back to its resting stroke (`:322-328` edge, `:377-382`
        gateway) and with the packet dropping to the next rail (orchestrator),
        and a predicate that strict would match none of them.

        A clear-down is: at least one `FadeOut`, nothing being introduced, and
        the camera staying put.
        """
        flat = list(self._walk(self._flatten(args)))
        if not any(isinstance(a, FadeOut) for a in flat):
            return False
        frame = camera._frame(self)
        for anim in flat:
            if isinstance(anim, FadeIn):
                return False
            if getattr(anim, "mobject", None) is frame:
                return False
        return True

    def play(self, *args: Animation, **kwargs):  # type: ignore[override]
        if self._in_split:
            return super().play(*args, **kwargs)
        if self._is_pure_wait(args):
            self._played_anything = True
            return super().play(*args, **kwargs)

        self._anim_n += 1
        merge_forward = self._prev_was_clear_down
        self._prev_was_clear_down = self._is_clear_down(args)

        # `next_slide()` ENDS the open slide and BEGINS a new one, so the
        # animation below lands in the NEW slide. Suppressing the call here is
        # therefore what merges this animation with the clear-down before it.
        if self._played_anything and not merge_forward:
            self._in_split = True
            try:
                self.next_slide(loop=self._anim_n == self.LOOP_ON_ANIMATION)
            finally:
                self._in_split = False
            self._stops += 1

        self._played_anything = True
        return super().play(*args, **kwargs)

    # -------------------------------------------------------------- construct
    def construct(self) -> None:
        # Mirrors `TheLifecycle.construct`'s prelude exactly: the beats depend
        # on `self.set` and `self.parcel` existing, and on the camera starting
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
        self.wait(self.END_HOLD)

        print(
            f"\n### slides: {self._anim_n} animations -> {self._stops} stops"
            f" (loop on animation {self.LOOP_ON_ANIMATION})",
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
