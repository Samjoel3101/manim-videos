"""The click-advanced deck of "What happens when you send a message to ChatGPT".

The generic machinery lives in `lib/slides.py`; the rules for authoring a scene
that converts cleanly are in `docs/slides.md`. This file holds only what is
specific to *this* film.

It is the shape a new video's deck should have: a base list, the counts, and
one `no_stops` region for the one repeat whose shape is the content. Nothing
here copies choreography — `ClickDeck.construct` calls `TheFactory.construct`
unchanged.

    .venv/bin/python scripts/build_slides.py chatgpt_message_journey

Known conversion defect, NOT worked around here: `beat_return`'s last play
combines `FadeOut(courier)` with `self.answer.body.animate.set_opacity(1.0)`
(`scenes/scene_factory.py:348-354`). A `.animate` opacity raise is not a
recognised arrival, so the play is classified as a clear-down and merges
forward into the three-word reveal after it. The deck loses one click; the film
is correct and is left alone. See `docs/slides.md` → "`.animate` is never an
arrival".
"""

from __future__ import annotations

import pathlib
import sys

from manim_slides import Slide

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SCENES = pathlib.Path(__file__).resolve().parent / "scenes"
for _p in (str(_ROOT), str(_SCENES)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib.components.transformer import LayerBlock  # noqa: E402
from lib.slides import ClickDeck  # noqa: E402
from scene_factory import TheFactory  # noqa: E402


class SlidesFactory(ClickDeck, Slide, TheFactory):
    """The whole film, cut into one click-advanced slide per animation."""

    EXPECTED_ANIMATIONS = 43
    EXPECTED_STOPS = 33

    def _sticky_play(self, args) -> bool:
        """The activation climbing the stack is a texture, not eight states.

        `scene_factory.py:255-257` pulses four `LayerBlock`s with an
        `activate`/`deactivate` pair each, inline in `beat_transform`. Every
        `deactivate` returns its block to exactly where it started, so split per
        play four of the eight clicks show the bay precisely as the click before
        it left it. The climb is one gesture, so it is one click — the same rule
        that gives the lifecycle film's decode ramp one click, and the opposite
        call from that film's decode-bay pulses, which advance their batch lanes
        a step per pulse and so are a sequence of distinct states.

        The loop is in the middle of a beat this deck may not edit, so the plays
        are recognised by what they animate rather than wrapped: a single
        `.animate` on a `LayerBlock`.
        """
        flat = self._flatten(args)
        if len(flat) != 1:
            return False
        return isinstance(getattr(flat[0], "mobject", None), LayerBlock)
