"""The click-advanced deck of "The lifecycle of a ChatGPT request".

The generic machinery lives in `lib/slides.py`; the rules for authoring a scene
that converts cleanly are in `docs/slides.md`. This file holds only what is
specific to *this* film: which animation loops, which repeats must not become
clicks, and the counts the split is expected to produce.

Nothing here copies choreography. `ClickDeck.construct` calls
`TheLifecycle.construct` unchanged, so `script.md` remains the single source of
truth for every timing in both outputs.

    .venv/bin/python scripts/build_slides.py chatgpt_request_lifecycle
"""

from __future__ import annotations

import pathlib
import sys

from manim import LaggedStart
from manim_slides import Slide

# The shipped scene imports its set as a sibling top-level module, so that
# directory goes on the path rather than being imported as a package.
_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SCENES = pathlib.Path(__file__).resolve().parent / "scenes"
for _p in (str(_ROOT), str(_SCENES)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib.components.chat_ui import TypingIndicator  # noqa: E402
from lib.slides import ClickDeck  # noqa: E402
from scene_lifecycle import TheLifecycle  # noqa: E402


class SlidesLifecycle(ClickDeck, Slide, TheLifecycle):
    """The whole film, cut into one click-advanced slide per animation."""

    #: Animation 3 is the `LaggedStart` that brings up the three dots of the
    #: typing indicator: the only animation in the film whose replay reads as a
    #: live idle rather than a value snapping back to its start. The back half's
    #: candidates — a token lapping the decode loop, a packet flying home — all
    #: end somewhere other than where they began, so looping them teleports the
    #: dot. Every other stop freezes, so a viewer can compare a frozen hold with
    #: an animated one in one sitting.
    LOOP_ON_ANIMATION = 3

    EXPECTED_ANIMATIONS = 97
    EXPECTED_STOPS = 70

    def _token_cycle(self, cycle, home, lap: float, emit: float, *,
                     comet: bool) -> None:
        """One decode step as ONE click — and the whole fast ramp as one more.

        The shipped cycle is two plays: lap the loop inside the box, then fly a
        token home and reveal one word. Split per play, the first of the two
        rests on a dot back where it started with no new word — a click that
        shows nothing. So each cycle is atomic.

        The two groups then differ, by the rule "keep stops unless the
        repetition is a ramp or a texture rather than a sequence of distinct
        states":

        * `CYCLES_EXPLICIT` (the four the film's own comment says the viewer is
          meant to COUNT) are a sequence of distinct states — one more word in
          the bubble each time — so they keep one click each. They are the
          `comet=True` calls.
        * `CYCLES_FAST` is a halving ramp, and `scene_lifecycle.py:174-186` says
          its shape IS the acceleration and that flattening it removes the one
          thing that reads as a machine speeding up. Six clicks would flatten it
          exactly as surely as re-timing it would; twelve (per play) worse. The
          whole ramp is ONE click, held open by `sticky_stops` because the six
          calls sit in the middle of a beat this deck may not edit. They are the
          `comet=False` calls — the film drops the comet below `EMIT_RUN_TIME`
          precisely because these are the fast ones, so the flag is the group,
          not a proxy for it.
        """
        region = self.no_stops() if comet else self.sticky_stops()
        with region:
            super()._token_cycle(cycle, home, lap, emit, comet=comet)

    def _is_loop_target(self, args) -> bool:
        """Is this play the typing-indicator's dots, i.e. what the loop claims?

        Checked at the split site rather than trusting the index: one
        `LaggedStart` whose members all animate dots belonging to a
        `TypingIndicator` currently on screen.
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
