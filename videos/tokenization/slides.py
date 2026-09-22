"""The click-advanced deck of "Tokenization: why the model never reads your words".

The generic machinery is in `lib/slides.py`; the rules for authoring a scene
that converts cleanly are in `docs/slides.md`. This file holds only what is
specific to THIS film — which repeats must not become clicks. It copies no
choreography: `ClickDeck.construct` runs `Tokenization.construct` unchanged, so
`script.md` stays the single source of truth for pacing in both outputs.

    .venv/bin/python scripts/build_slides.py tokenization --probe   # seconds
    .venv/bin/python scripts/build_slides.py tokenization           # render + HTML
"""

from __future__ import annotations

import pathlib
import sys

from manim_slides import Slide

# The shipped scene imports its set as a sibling top-level module, so that
# directory goes on the path rather than being imported as a package.
_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SCENES = pathlib.Path(__file__).resolve().parent / "scenes"
for _p in (str(_ROOT), str(_SCENES)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib.slides import ClickDeck  # noqa: E402
from scene_tokenization import Tokenization  # noqa: E402


class SlidesTokenization(ClickDeck, Slide, Tokenization):
    """The whole film, cut into one click-advanced slide per animation.

    Nothing in this film loops: `LOOP_ON_ANIMATION` is deliberately unset. A
    loop is honest only for an animation that ends where it began — a live idle
    — and every candidate here (the wipe, the flight along the rail, the merge
    snaps, the bars filling, the bench shrinking into the ghost node) ends
    somewhere other than where it started, so looping one would teleport on
    replay.
    """

    EXPECTED_ANIMATIONS = 45
    EXPECTED_STOPS = 42

    def merge_ramp(self) -> None:
        """Beat 3's runaway merge list as ONE click.

        By the rule in `docs/slides.md` §2.4 — keep the stops unless the repeat
        is a ramp or a texture rather than a sequence of distinct states. This
        is a single play already, but it is wrapped rather than left bare so the
        intent is stated where a future edit that splits it into several plays
        will read it: the list accelerating out of legibility is one gesture,
        and clicking through it frame by frame flattens the one thing it says.
        """
        with self.no_stops():
            super().merge_ramp()
