"""Rows of named checks that tick from pending to passed.

Half the machines in a request pipeline do the same thing: they run a short list
of named checks and let the request through. An edge tier checks the firewall,
the bot score and the rate limit; a gateway checks the session, the plan and the
quota; a streaming tier checks detokenisation, output safety and whether a tool
was called. Drawing that as "a list of things, each of which goes green" is the
single most reusable shape in the format, so it lives here rather than in a
video.

Two construction rules, both of which are scar tissue:

**Reserve the columns; do not measure the text.** Laying a row out around its own
label — ``marker.next_to(label, LEFT)`` — puts every row's marker wherever that
row's word happened to start, and a list of "WAF" and "rate limit" comes out
with a ragged left edge. (That is the same bug session 7 fixed in
``ProbabilityBar``; it is worth fixing once per component because alignment is
invisible to the snapshot gate — a 16x16 luminance signature cannot see a marker
move a third of a unit.) Every row here is built against a fixed origin instead:
the marker's left edge at x=0, the label at a constant offset, the detail
right-aligned inside a reserved right column ``width`` wide. A plain
``arrange(DOWN, aligned_edge=LEFT)`` then lines up all three columns at once, and
:func:`tests.test_components_structure` asserts it.

**The tick is stroke-only, so it fades on stroke.** A tick built from two
``Line``s carries its colour in the stroke with no fill at all. A blanket
``set_opacity`` raises fill opacity too, and the two strokes come back as a pair
of filled slivers. This is the third time this repo has been bitten by
fill-vs-stroke — the glow halos in session 5, the Lucide icon blobs in session 6
— and every time it presented as "the colour is wrong" rather than as what it
was. :meth:`CheckRow.mark_pass` only ever touches ``set_stroke``/``set_fill``
explicitly; never call ``set_opacity`` on ``CheckRow.tick`` or ``CheckRow.cross``.

The mutators are deliberately safe under ``.animate``: they change fill, stroke
and colour only, and never the submobject list. ``row.animate.mark_pass()`` is
the intended call site, and rebuilding the label text inside ``mark_pass`` — the
obvious way to also change the wording — would break interpolation the same way
``ProbabilityBar.set_value`` does.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from manim import DOWN, LEFT, ORIGIN, RIGHT, Circle, Line, VGroup

from lib import theme, typography, utils

#: Shot width these rows are typed for when the caller does not say.
#:
#: 13.6 is the house close-up: a 9.6-wide station bay with margin at 16:9 (see
#: any ``*_set.py``'s ``SHOT_TIGHT``). It is a default rather than a required
#: argument for the same reason ``Station.shot_width`` has one — a component
#: dropped into a test or a snapshot case should construct without the caller
#: having to invent a camera — but a scene should always pass its own.
DEFAULT_FRAME_WIDTH = 13.6

#: States a row can be in. ``mark_fail`` exists because a pipeline diagram that
#: can only show success quietly teaches that these checks never reject anything.
PENDING, PASSED, FAILED = "pending", "passed", "failed"


class CheckRow(VGroup):
    """One named check: a marker, a label, and an optional right-hand detail.

    Parameters
    ----------
    label:
        What is being checked — "bot score", "quota", "output safety".
    detail:
        The measured value, right-aligned in a reserved column: "0.02",
        "12 / 60", "pro → gpt-5". Optional, and a list may mix rows with and
        without one; the columns still line up because the column is reserved
        rather than measured.
    color:
        The accent a passing row turns. Defaults to :data:`lib.theme.ASSISTANT`
        — green means passed, everywhere in the series.
    width:
        The row's reserved width. The detail's right edge lands on it, so every
        row in a list agrees on where the right-hand column is.
    marker_size:
        Diameter of the circle. The tick is drawn inside it and scales with it.
    frame_width:
        The shot this row's type is sized for. See :mod:`lib.typography`.
    """

    def __init__(
        self,
        label: str,
        *,
        detail: str | None = None,
        color=None,
        width: float = 3.4,
        marker_size: float = 0.17,
        frame_width: float = DEFAULT_FRAME_WIDTH,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.accent = color or theme.ASSISTANT
        self.label = label
        self.row_width = width
        self.marker_size = marker_size
        self.state = PENDING

        radius = marker_size / 2.0
        # A stroke scaled off the marker so a big row and a small row read the
        # same. The floor stops a tiny marker rendering as a hairline smudge.
        mark_stroke = max(1.4, marker_size * 18.0)

        # -- the marker, at a FIXED origin: left edge on x=0 -------------------
        self.marker = Circle(
            radius=radius,
            stroke_color=theme.FG_FAINT,
            stroke_width=theme.STROKE_NORMAL,
            fill_color=theme.SURFACE,
            fill_opacity=1.0,
        )
        self.marker.move_to(np.array([radius, 0.0, 0.0]))

        # -- the tick and the cross, both pre-built and both dark --------------
        # Pre-built rather than added on demand: `mark_pass` has to leave the
        # submobject list alone to stay safe under `.animate`, so both marks
        # exist from the start and only their stroke opacity moves. They are
        # drawn in the background colour because they sit on top of a disc that
        # fills with the accent — a green tick on a green disc is invisible.
        self.tick = self._tick(radius, mark_stroke)
        self.cross = self._cross(radius, mark_stroke)
        for mark in (self.tick, self.cross):
            mark.move_to(self.marker.get_center())
            mark.set_stroke(opacity=0.0)

        # -- the detail column, reserved on the right -------------------------
        self.detail_mob = None
        detail_width = 0.0
        if detail:
            self.detail_mob = typography.text(
                "micro", detail, frame_width=frame_width,
                color=theme.FG_MUTED, mono=True,
            )
            utils.fit_text(self.detail_mob, width * 0.42)
            detail_width = self.detail_mob.width

        # -- the label, clamped so it can never run into the detail column ----
        self.label_mob = typography.text(
            "label", label, frame_width=frame_width, color=theme.FG_MUTED
        )
        label_left = marker_size + theme.PAD_SM
        room = width - label_left - detail_width - (theme.PAD_SM if detail else 0.0)
        utils.fit_text(self.label_mob, max(room, 0.2))

        self.label_mob.set_y(0.0)
        self.label_mob.shift(RIGHT * (label_left - self.label_mob.get_left()[0]))
        if self.detail_mob is not None:
            self.detail_mob.set_y(0.0)
            self.detail_mob.shift(
                RIGHT * (width - self.detail_mob.get_right()[0])
            )

        self.add(self.marker, self.tick, self.cross, self.label_mob)
        if self.detail_mob is not None:
            self.add(self.detail_mob)

    # ------------------------------------------------------------- geometry
    @staticmethod
    def _tick(radius: float, stroke_width: float) -> VGroup:
        """A check mark as two lines, stroke-only. Never give this a fill."""
        a = np.array([-0.46 * radius, 0.04 * radius, 0.0])
        b = np.array([-0.12 * radius, -0.36 * radius, 0.0])
        c = np.array([0.48 * radius, 0.40 * radius, 0.0])
        return VGroup(
            Line(a, b, stroke_color=theme.BG, stroke_width=stroke_width),
            Line(b, c, stroke_color=theme.BG, stroke_width=stroke_width),
        )

    @staticmethod
    def _cross(radius: float, stroke_width: float) -> VGroup:
        """The failure mark. A red *tick* would read as "passed, but bad"."""
        r = 0.34 * radius
        return VGroup(
            Line(
                np.array([-r, -r, 0.0]), np.array([r, r, 0.0]),
                stroke_color=theme.BG, stroke_width=stroke_width,
            ),
            Line(
                np.array([-r, r, 0.0]), np.array([r, -r, 0.0]),
                stroke_color=theme.BG, stroke_width=stroke_width,
            ),
        )

    # --------------------------------------------------------------- states
    def mark_pass(self) -> "CheckRow":
        """Tick this row. Safe inside ``.animate``: colour and opacity only."""
        self.marker.set_fill(self.accent, opacity=1.0)
        self.marker.set_stroke(self.accent, width=theme.STROKE_NORMAL)
        # Stroke, not `set_opacity`. See the module docstring: the tick has no
        # fill at all and raising its fill opacity draws two filled slivers.
        self.tick.set_stroke(opacity=1.0)
        self.cross.set_stroke(opacity=0.0)
        self.label_mob.set_color(theme.FG)
        self.state = PASSED
        return self

    def mark_fail(self) -> "CheckRow":
        """Fail this row, in :data:`lib.theme.ERROR`. Same animation rules."""
        self.marker.set_fill(theme.ERROR, opacity=1.0)
        self.marker.set_stroke(theme.ERROR, width=theme.STROKE_NORMAL)
        self.tick.set_stroke(opacity=0.0)
        self.cross.set_stroke(opacity=1.0)
        self.label_mob.set_color(theme.ERROR)
        self.state = FAILED
        return self

    def reset(self) -> "CheckRow":
        """Back to pending — an empty outline and a muted label."""
        self.marker.set_fill(theme.SURFACE, opacity=1.0)
        self.marker.set_stroke(theme.FG_FAINT, width=theme.STROKE_NORMAL)
        self.tick.set_stroke(opacity=0.0)
        self.cross.set_stroke(opacity=0.0)
        self.label_mob.set_color(theme.FG_MUTED)
        self.state = PENDING
        return self


class CheckList(VGroup):
    """A column of :class:`CheckRow`s that share their three column edges.

    ``rows`` is a sequence of labels, or ``(label, detail)`` pairs, or any mix:

    >>> CheckList(["WAF", ("bot score", "0.02"), ("rate limit", "12 / 60")])

    The rows are arranged with ``aligned_edge=LEFT``, which is only enough
    because every row's bounding box already starts at its own x=0 — see the
    module docstring on reserving columns.
    """

    def __init__(
        self,
        rows: Sequence[str | tuple[str, str]],
        *,
        width: float = 3.4,
        color=None,
        gap: float = theme.PAD_SM,
        marker_size: float = 0.17,
        frame_width: float = DEFAULT_FRAME_WIDTH,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if not rows:
            raise ValueError("CheckList needs at least one row")
        self.accent = color or theme.ASSISTANT
        self.list_width = width

        built = []
        for item in rows:
            if isinstance(item, str):
                label, detail = item, None
            else:
                label, detail = item[0], item[1]
            built.append(
                CheckRow(
                    label,
                    detail=detail,
                    color=self.accent,
                    width=width,
                    marker_size=marker_size,
                    frame_width=frame_width,
                )
            )
        self.rows = VGroup(*built).arrange(DOWN, buff=gap, aligned_edge=LEFT)
        self.add(self.rows)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index):  # type: ignore[override]
        return self.rows[index]

    def row_for(self, label: str) -> CheckRow | None:
        for row in self.rows:
            if row.label == label:
                return row
        return None

    def pass_all(self) -> list:
        """Animation builders ticking every row, for a ``LaggedStart``.

        Returned rather than played so the choreography owns the lag and the
        easing — the same reason ``camera.focus`` returns an animation.
        """
        return [row.animate.mark_pass() for row in self.rows]

    def reset(self) -> "CheckList":
        for row in self.rows:
            row.reset()
        return self


__all__ = ["CheckRow", "CheckList", "PENDING", "PASSED", "FAILED",
           "DEFAULT_FRAME_WIDTH"]
