"""One-off visuals that only this film needs.

AGENTS rule 2: a thing is promoted into ``/lib`` when a *second* scene needs it,
not in anticipation. Each of these has exactly one call site in
``scene_lifecycle.py``, so they live here. If another video ever wants one, that
is the moment to move it — and the moment to give it a structural test and a
snapshot baseline, which is what ``/lib`` membership costs.

Two of the three (``RequestCard``, ``BatchLanes``) are near misses for promotion
and are written as if they were already in ``/lib``: reserved columns rather than
measured text, mutators that are safe under ``.animate``, type through
``lib.typography`` with an explicit ``frame_width``. That is cheap now and is the
difference between a five-minute promotion and a rewrite.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, RoundedRectangle, VGroup

from lib import theme, typography, utils


class RequestCard(VGroup):
    """A titled panel of ``key  value`` rows: the HTTP request, drawn.

    Shown once, beside the chat, to make the point that "hitting send" builds a
    document with a lot more in it than the sentence you typed. It is a
    **close-up-only prop**: the scene fades it out at the end of its beat,
    because a card sized to be read at width 18 is unreadable litter at the
    45-unit pull-back, and it is deliberately not part of
    ``LifecycleSet.everything`` so that a prop which is no longer on screen
    cannot widen ``SHOT_WIDE``.

    Same column rule as everything else in this repo: the key column is
    *reserved*, so every value starts at the same x whatever its key says. Laying
    each row out as ``value.next_to(key)`` is how a table comes out with a ragged
    middle edge, and the snapshot gate cannot see it.
    """

    def __init__(
        self,
        rows: Sequence[tuple[str, str]],
        *,
        title: str = "POST /v1/chat",
        width: float = 5.6,
        key_column: float = 1.7,
        frame_width: float = 18.0,
        accent=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if not rows:
            raise ValueError("RequestCard needs at least one row")
        self.accent = accent or theme.USER

        self.title_mob = typography.text(
            "label", title, frame_width=frame_width, color=self.accent,
            mono=True, bold=True,
        )
        utils.fit_text(self.title_mob, width - 2 * theme.PAD_MD)

        built = VGroup()
        value_room = width - 2 * theme.PAD_MD - key_column - theme.PAD_SM
        for key, value in rows:
            key_mob = typography.text(
                "micro", key, frame_width=frame_width,
                color=theme.FG_MUTED, mono=True,
            )
            utils.fit_text(key_mob, key_column)
            value_mob = typography.text(
                "micro", value, frame_width=frame_width, color=theme.FG, mono=True
            )
            utils.fit_text(value_mob, value_room)
            # Fixed origin: key left edge at 0, value left edge always at
            # key_column + PAD_SM, whatever the key happened to be.
            key_mob.set_y(0.0)
            key_mob.shift(RIGHT * -key_mob.get_left()[0])
            value_mob.set_y(0.0)
            value_mob.shift(
                RIGHT * (key_column + theme.PAD_SM - value_mob.get_left()[0])
            )
            built.add(VGroup(key_mob, value_mob))
        built.arrange(DOWN, buff=theme.PAD_XS, aligned_edge=LEFT)
        self.rows = built

        body = VGroup(self.title_mob, built).arrange(
            DOWN, buff=theme.PAD_SM, aligned_edge=LEFT
        )
        self.panel = utils.panel(
            width=max(width, body.width + 2 * theme.PAD_MD),
            height=body.height + 2 * theme.PAD_MD,
            fill=theme.BG_ELEVATED,
            stroke=self.accent,
            stroke_width=theme.STROKE_NORMAL,
        )
        body.move_to(self.panel.get_center())
        self.add(self.panel, body)


class StampChip(VGroup):
    """A small pill that rides along with the packet — "this has been stamped".

    The visual grammar of the first third of the film: the payload is never
    replaced, it only accumulates evidence that machines have touched it. A
    proof-of-work stamp, then a trace id.

    Attached by ``next_to``-ing it to the packet once and then moving the pair as
    a ``VGroup``. ``always_redraw`` was considered and is not needed: an updater
    re-evaluates every frame for the whole remaining film, which is a real cost
    for something that only has to stay put relative to one dot.
    """

    def __init__(
        self,
        text: str,
        *,
        color=None,
        frame_width: float = 16.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.accent = color or theme.WARN
        self.text_mob = typography.text(
            "micro", text, frame_width=frame_width, color=self.accent, mono=True
        )
        self.pill = RoundedRectangle(
            width=self.text_mob.width + 2 * theme.PAD_SM,
            height=self.text_mob.height + 2 * theme.PAD_XS,
            corner_radius=(self.text_mob.height + 2 * theme.PAD_XS) / 2,
            fill_color=theme.BG_ELEVATED,
            fill_opacity=1.0,
            stroke_color=self.accent,
            stroke_width=theme.STROKE_HAIRLINE,
        )
        self.text_mob.move_to(self.pill.get_center())
        self.add(self.pill, self.text_mob)


class BatchLanes(VGroup):
    """Several requests being decoded together, one row each, stepping in lockstep.

    The point of the beat: your request is not alone on the GPU. One row is
    yours (``mine``) and is drawn in :data:`lib.theme.TOKEN`; the rest are
    strangers' and are drawn faint. Every call to :meth:`step` fills one more
    chip in *every* row at once, because that is what batched decoding does —
    one token per step, for everybody, simultaneously.

    Only the highlighted row is labelled. Naming the muted rows was tried on
    paper and rejected: at this size — the whole widget is under two units wide
    inside a 9.6 bay — four more words is noise, and the colour already says
    which row the viewer is meant to follow.

    :meth:`step` changes fill opacity only and never the submobject list, so
    ``lanes.animate.step()`` interpolates cleanly.
    """

    def __init__(
        self,
        *,
        lanes: int = 4,
        mine: int = 1,
        steps: int = 3,
        chip: float = 0.22,
        frame_width: float = 13.6,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if not 0 <= mine < lanes:
            raise ValueError("`mine` must index one of the lanes")
        self.lane_count = lanes
        self.step_count = steps
        self.mine = mine
        self.filled = 0

        self.rows = VGroup()
        for row in range(lanes):
            accent = theme.TOKEN if row == mine else theme.FG_FAINT
            cells = VGroup(
                *[
                    RoundedRectangle(
                        width=chip,
                        height=chip * 0.72,
                        corner_radius=chip * 0.18,
                        fill_color=accent,
                        fill_opacity=0.0,
                        stroke_color=theme.FG_FAINT,
                        stroke_width=theme.STROKE_HAIRLINE,
                    )
                    for _ in range(steps)
                ]
            ).arrange(RIGHT, buff=theme.PAD_XS * 0.6)
            self.rows.add(cells)
        self.rows.arrange(DOWN, buff=theme.PAD_XS * 0.6, aligned_edge=LEFT)

        # The label hangs off the left of the one row that matters, so the grid
        # itself stays a grid.
        self.label_mob = typography.text(
            "micro", "you", frame_width=frame_width, color=theme.TOKEN
        )
        self.label_mob.next_to(self.rows[mine], LEFT, buff=theme.PAD_XS)
        self.add(self.rows, self.label_mob)

    def step(self, count: int = 1) -> "BatchLanes":
        """Fill one more column in every lane. Safe inside ``.animate``."""
        self.filled = max(0, min(self.filled + count, self.step_count))
        for row in self.rows:
            for i, cell in enumerate(row):
                cell.set_fill(opacity=1.0 if i < self.filled else 0.0)
        return self

    def reset(self) -> "BatchLanes":
        self.filled = 0
        for row in self.rows:
            for cell in row:
                cell.set_fill(opacity=0.0)
        return self


__all__ = ["RequestCard", "StampChip", "BatchLanes"]
