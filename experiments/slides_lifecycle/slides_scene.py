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
"""

from __future__ import annotations

import pathlib
import sys

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
    """The top band of the film, cut into four click-advanced slides."""

    #: A beat's last frame is never its finished composition. Each shipped beat
    #: ends on a FadeOut, and manim renders an animation's final frame at
    #: t = run_time - 1/fps, so the fading props are still faintly drawn when
    #: the chunk is cut. In the continuous take the next beat covers that frame
    #: 1/60 s later; a click stop promotes it into the held still. FadeOut has
    #: already REMOVED the mobjects by then, so a few still frames after the
    #: beat — and before the stop — rest on the clean composition instead.
    SETTLE = 0.2

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
        self.wait(self.SETTLE)
        self.next_slide()

        self.beat_edge()
        self.wait(self.SETTLE)
        self.next_slide()

        self.beat_gateway()
        self.wait(self.SETTLE)
        # The one animated hold in the deck. Every other stop freezes on its
        # last frame while it waits for a click; this one replays instead, so
        # the contrast between a frozen pause and a live idle is visible in a
        # single sitting. That contrast is the thing this spike asks the viewer
        # to judge.
        self.next_slide(loop=True)

        self.beat_orchestrator()
