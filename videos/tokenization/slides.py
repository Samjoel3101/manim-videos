"""The click-advanced deck of "Tokenization: why the model never reads your words".

The generic machinery is in `lib/slides.py`; the rules for authoring a scene
that converts cleanly are in `docs/slides.md`. This file holds only what is
specific to THIS film — which repeats must not become clicks. It copies no
choreography: `ClickDeck.construct` runs the shipped `construct` unchanged, so
`script.md` stays the single source of truth for pacing in both outputs.

    .venv/bin/python scripts/build_slides.py tokenization --probe   # seconds
    .venv/bin/python scripts/build_slides.py tokenization           # render + HTML

One suppressed region, not the two the plan anticipated:

* **B3's merge ramp** — four plays in which the ordered list scrolls up out of
  legibility while the counter runs `merge 4` -> `merge 50,000`. Its SHAPE is
  the content, so it is one click. It is written inline in a beat this deck may
  not edit, so it is recognised by what it animates (`tokenizer_props.RampTicker`) rather
  than by a play index — an index moves silently when a beat is re-ordered.

* **B6's ghost assembly and set-shrink** needs no suppression at all: the
  bench's `Transform` and the circuit's `FadeIn` are a single `self.play`, so
  it is already one click. `no_stops()` around a single play would only add a
  region to the report.
"""

from __future__ import annotations

import pathlib
import sys

from manim import FadeIn
from manim_slides import Slide

# The shipped scene imports its set as a sibling top-level module, so that
# directory goes on the path rather than being imported as a package.
_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SCENES = pathlib.Path(__file__).resolve().parent / "scenes"
for _p in (str(_ROOT), str(_SCENES)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib.slides import ClickDeck  # noqa: E402
from tokenizer_props import RampTicker  # noqa: E402
from scene_tokenization import TheTokenizer  # noqa: E402


class SlidesTokenizer(ClickDeck, Slide, TheTokenizer):
    """The whole film, cut into one click-advanced slide per animation."""

    EXPECTED_ANIMATIONS = 47
    EXPECTED_STOPS = 40

    def _sticky_play(self, args) -> bool:
        """B3's merge ramp is one gesture, so it is one click.

        `scene_tokenization.beat_the_table` runs four plays that scroll the
        ordered list up out of legibility while the counter runs `merge 4` ->
        `merge 50,000`. The film's own comment says the shape of that
        acceleration IS the content — split per play, four clicks flatten it as
        surely as re-timing it would. The same call the lifecycle film makes for
        its `CYCLES_FAST` decode ramp.

        Recognised by mobject, never by index: every ramp play fades a
        `RampTicker` IN, and nothing else in the film does. The `FadeIn` test
        matters — B4's clear-down fades the last ticker OUT along with the rest
        of the table, and matching on the mobject alone opened a second region
        there.
        """
        return any(
            isinstance(anim, FadeIn)
            and isinstance(getattr(anim, "mobject", None), RampTicker)
            for anim in self._flatten(args)
        )
