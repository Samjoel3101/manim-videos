"""Proportional stacked bars: "what is this thing actually made of".

The shape exists for one recurring beat — *your* contribution to something is
much smaller than you think. A chat prompt is a system message, a pile of tool
definitions, some memory, and then your question; a forward pass is a cached
prefix and a short new tail. Drawing that as one bar cut into labelled segments
says it in a frame, where a sentence would need narration.

``min_segment`` is the whole point of the component
---------------------------------------------------

Seven tokens out of 3,937 is 0.18% of the bar. At any reasonable length that is
under a pixel: the segment does not render, and the beat — "your question is the
last few tokens of about four thousand" — fails silently, with the bar looking
like it has one fewer part than the legend claims.

So a segment's **drawn** fraction is clamped to at least ``min_segment`` and the
others are renormalised so the drawn widths still fill the bar. The **values
stay true**: the legend prints the real number, and :attr:`SegmentedBar.fractions`
reports the unclamped arithmetic for anything that needs it.

This is the same trade ``tokens.display_token``'s ``show_space`` makes, and for
the same reason: in a silent cut, legibility beats notation. A viewer who cannot
see the segment learns nothing true from its absence, and the model keeps the
real number either way. If you need the honest picture — a bar where a 0.18%
slice really is 0.18% — pass ``min_segment=0``.

Column discipline
-----------------

The legend is a table, so it is built against a fixed origin like every other
row in this repo (swatch at x=0, name at a constant offset, value right-aligned
inside a reserved column). Laying each row out around its own name gives
"memory + prefs" and "your message" different value positions, which reads as a
sloppy chart and is invisible to the snapshot gate. See
``lib/components/checks.py`` for the longer version of this note.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
from manim import DOWN, LEFT, RIGHT, Rectangle, VGroup

from lib import theme, typography, utils

#: Shot width the labels are typed for when the caller does not say. See
#: :data:`lib.components.checks.DEFAULT_FRAME_WIDTH`.
DEFAULT_FRAME_WIDTH = 13.6

#: Drawn fraction below which an inline label is simply omitted. Squeezing
#: "memory + prefs" into 8% of a 5-unit bar produces a smear, not a label — that
#: is what :meth:`SegmentedBar.emphasise` plus a caption is for.
#:
#: A segment at or above this floor keeps its label, and that label is typed at
#: a readable size even where that means overhanging its own segment — see
#: ``_build_inline``. ``min_segment`` below this value in ``labels="inline"``
#: mode is refused by the constructor, because the two constants used to fight
#: each other silently: the caller floored a sliver to make it visible and the
#: label rule here then dropped its name and number.
INLINE_MIN_FRACTION = 0.12

LABEL_MODES = ("legend", "inline", "none")

#: Where a ``labels="legend"`` table is placed relative to the bar.
LEGEND_SIDES = ("right", "below")

#: The type role both legend columns are drawn at. Named rather than repeated
#: as a literal because ``_build_legend``'s readability guard tests this role's
#: fraction against the scale it applied: if the drawn role and the checked
#: role ever drift apart, the guard silently starts grading the wrong thing.
LEGEND_ROLE = "micro"


class SegmentedBar(VGroup):
    """A proportional bar cut into named, coloured segments.

    Parameters
    ----------
    segments:
        ``{"system prompt": 2400, "your message": 7}`` or a sequence of
        ``(name, value)`` pairs, in draw order left to right.
    length, thickness:
        The bar's full extent. Segment widths sum to ``length`` minus the gaps.
    colors:
        One colour per segment. Defaults to cycling :data:`lib.theme.SERIES`.
    labels:
        ``"legend"`` (a table to the right), ``"inline"`` (names under the
        segments) or ``"none"``.
    show_values:
        Whether the label carries the number as well as the name.
    value_format:
        ``str.format`` spec for that number. The default groups thousands,
        because the numbers this component draws are usually token counts.
    min_segment:
        Floor on a segment's *drawn* fraction. See the module docstring. In
        ``labels="inline"`` mode it must be at least
        :data:`INLINE_MIN_FRACTION` (or ``0``), or the floored segments come out
        drawn but unlabelled — see ``allow_unlabelled_segments``.
    allow_unlabelled_segments:
        Opt in to ``min_segment`` below :data:`INLINE_MIN_FRACTION` in inline
        mode, for the case where something else on screen names the sliver.
    gap:
        Space between segments. Zero — one solid bar — by default.
    legend_side:
        ``"right"`` (the default: a table beside the bar) or ``"below"`` (a
        table under the bar, sharing its left edge and its full width). Beside
        a short bar in a station bay there is room for the numbers but not for
        the words; below it there is room for both at the same size.
    legend_width:
        Width of the legend table. Defaults to ``length * 0.85`` beside the bar
        and to ``length`` below it.
    strict_legend:
        Refuse to draw a legend whose one type size would fall below
        :data:`lib.typography.MIN_READABLE` at ``frame_width``, rather than
        drawing words nobody can read. Off by default so existing callers keep
        working; on for anything whose legibility matters.
    """

    def __init__(
        self,
        segments: Mapping[str, float] | Sequence[tuple[str, float]],
        *,
        length: float = 5.0,
        thickness: float = 0.5,
        colors: Sequence | None = None,
        labels: str = "legend",
        show_values: bool = True,
        value_format: str = "{:,.0f}",
        min_segment: float = 0.02,
        gap: float = 0.0,
        legend_width: float | None = None,
        legend_side: str = "right",
        strict_legend: bool = False,
        frame_width: float = DEFAULT_FRAME_WIDTH,
        allow_unlabelled_segments: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if labels not in LABEL_MODES:
            raise ValueError(f"labels must be one of {LABEL_MODES}")
        if legend_side not in LEGEND_SIDES:
            raise ValueError(f"legend_side must be one of {LEGEND_SIDES}")

        items = list(segments.items()) if hasattr(segments, "items") else list(segments)
        if not items:
            raise ValueError("SegmentedBar needs at least one segment")
        if min_segment * len(items) > 1.0:
            raise ValueError(
                f"min_segment={min_segment} cannot be honoured for {len(items)} "
                "segments — the floors alone would overflow the bar"
            )

        # Two module constants used to fight each other in silence: a caller
        # would pass `min_segment=0.05` to make a sliver visible, and
        # `_build_inline` would then drop that sliver's label because 0.05 is
        # under INLINE_MIN_FRACTION (0.12). The floored segment was drawn and
        # its name and number were not, so the beat the floor existed for showed
        # a coloured stripe with nothing saying what it was. That is exactly
        # what happened to the prefill/KV bar in chatgpt_request_lifecycle: the
        # "37" the beat is about was never on screen.
        #
        # Dropping a too-narrow label is still the right behaviour (a name
        # squeezed into 5% of a bar is a smear), so this does not change it —
        # it makes the caller say out loud that they meant it.
        if (
            labels == "inline"
            and 0 < min_segment < INLINE_MIN_FRACTION
            and not allow_unlabelled_segments
        ):
            raise ValueError(
                f"min_segment={min_segment} is below INLINE_MIN_FRACTION="
                f"{INLINE_MIN_FRACTION}, so every segment held up by the floor "
                "will be DRAWN and left UNLABELLED in labels='inline' mode. "
                f"Either raise min_segment to at least {INLINE_MIN_FRACTION} so "
                "the segment carries its own name and value, or pass "
                "allow_unlabelled_segments=True if a caption elsewhere names it."
            )

        self.names = [str(name) for name, _ in items]
        self.values = [float(value) for _, value in items]
        self.bar_length = length
        self.thickness = thickness
        self.value_format = value_format
        self.label_mode = labels
        self.min_segment = min_segment
        self._shown = len(items)

        self.colors = (
            list(colors)
            if colors is not None
            else [theme.series_color(i) for i in range(len(items))]
        )

        self._fractions = self._true_fractions(self.values)
        self.drawn_fractions = self._clamped_fractions(self._fractions, min_segment)

        # Segment widths sum to the bar minus its gaps, so the drawn bar is
        # exactly `length` wide however many parts it has.
        self.drawn_length = length - gap * (len(items) - 1)
        widths = [f * self.drawn_length for f in self.drawn_fractions]

        # -- the bar, built from a FIXED origin: left edge on x=0 -------------
        self.segments = VGroup()
        cursor = 0.0
        for i, w in enumerate(widths):
            rect = Rectangle(
                width=max(w, 1e-4),
                height=thickness,
                fill_color=self.colors[i % len(self.colors)],
                fill_opacity=1.0,
                stroke_width=0,
            )
            rect.move_to(np.array([cursor + w / 2.0, 0.0, 0.0]))
            self.segments.add(rect)
            cursor += w + gap
        self.add(self.segments)

        #: One entry per segment, parallel to :attr:`segments`. Empty groups for
        #: segments with no label, so index arithmetic never has to special-case
        #: them and the submobject list stays constant under ``.animate``.
        self.label_groups: list[VGroup] = []
        self.legend = None
        self.legend_side = legend_side
        if labels == "legend":
            if legend_width is not None:
                width = legend_width
            elif legend_side == "below":
                # Below the bar the legend has the bar's own width to spend —
                # that is the entire point of the placement.
                width = length
            else:
                width = length * 0.85
            self._build_legend(
                length=length,
                legend_width=width,
                show_values=show_values,
                frame_width=frame_width,
                legend_side=legend_side,
                strict_legend=strict_legend,
            )
        elif labels == "inline":
            self._build_inline(widths, show_values, frame_width)
        else:
            self.label_groups = [VGroup() for _ in items]

    # ----------------------------------------------------------- arithmetic
    @staticmethod
    def _true_fractions(values: Sequence[float]) -> list[float]:
        total = float(sum(values))
        if total <= 0:
            # An all-zero bar is a caller error rather than a crash: draw it as
            # equal parts so the beat still shows the right number of things.
            return [1.0 / len(values)] * len(values)
        return [v / total for v in values]

    @staticmethod
    def _clamped_fractions(fractions: Sequence[float], floor: float) -> list[float]:
        """Fractions with every entry at least ``floor``, still summing to 1.

        Iterative, because lifting the small segments shrinks the big ones and
        can push another one under the floor. Each pass pins everything already
        at or below the floor and redistributes what is left in proportion to
        the *true* fractions, so the visible ordering of the honest segments is
        never disturbed.
        """
        if floor <= 0:
            return list(fractions)
        pinned = set()
        for _ in range(len(fractions) + 1):
            free = [i for i in range(len(fractions)) if i not in pinned]
            budget = 1.0 - floor * len(pinned)
            free_total = sum(fractions[i] for i in free)
            scale = (budget / free_total) if free_total > 0 else 0.0
            newly = [i for i in free if fractions[i] * scale < floor]
            if not newly:
                out = [0.0] * len(fractions)
                for i in pinned:
                    out[i] = floor
                for i in free:
                    out[i] = fractions[i] * scale
                return out
            pinned.update(newly)
        # Everything hit the floor: the constructor's guard makes this
        # unreachable for min_segment * n <= 1, but fall back to equal parts.
        return [1.0 / len(fractions)] * len(fractions)

    @property
    def fractions(self) -> list[float]:
        """The TRUE fractions, unclamped. What the data says, not what is drawn."""
        return list(self._fractions)

    # --------------------------------------------------------------- labels
    def _value_text(self, index: int) -> str:
        return self.value_format.format(self.values[index])

    def _build_legend(
        self, *, length: float, legend_width: float, show_values: bool,
        frame_width: float, legend_side: str, strict_legend: bool,
    ) -> None:
        swatch = self.thickness * 0.5

        # The value COLUMN, reserved once for every row — not each row's own
        # value width. An earlier version measured `value_mob.width` inside the
        # loop and subtracted that from the room left for the name, so the row
        # whose value was "7" handed its name 0.3 more units than the row whose
        # value was "2,400", and only the latter got shrunk by `fit_text`. The
        # legend then came out with names at four different sizes (measured
        # heights 0.1369 / 0.1155 / 0.1687 / 0.1766 on this film's own data —
        # a 53% spread, and not even monotone in name length), which reads as a
        # sloppy chart. The row edges stayed perfectly aligned throughout, which
        # is why the structural test that checks edges never saw it, and why the
        # 16x16 luminance snapshot did not either.
        value_mobs: list = []
        if show_values:
            value_mobs = [
                typography.text(
                    LEGEND_ROLE, self._value_text(i), frame_width=frame_width,
                    color=theme.FG_MUTED, mono=True,
                )
                for i in range(len(self.names))
            ]

        name_mobs = [
            typography.text(
                LEGEND_ROLE, name, frame_width=frame_width, color=theme.FG
            )
            for name in self.names
        ]

        # ONE type size for the whole legend. The previous version ran only the
        # NAME through `fit_text` and never the value, so on this film's own
        # data every name came out 0.26-0.35x the height of its own number:
        # measured shares 0.0066-0.0077 of frame height against a
        # typography.MIN_READABLE of 0.020, while every value cleared the floor.
        # That is the same "drawn and unreadable" failure `_build_inline` guards
        # against, one column over, and it reads as a chart whose words have
        # been squashed rather than as a legend.
        #
        # So the columns are sized TOGETHER: work out the one factor that makes
        # the widest row fit, and apply it to names and values alike. The row is
        # swatch + PAD_SM + name + PAD_SM + value, of which only the two text
        # columns can scale, so the factor is exact rather than iterated.
        name_width = max(mob.width for mob in name_mobs)
        value_width = max((mob.width for mob in value_mobs), default=0.0)
        name_left = swatch + theme.PAD_SM
        text_room = legend_width - name_left - (theme.PAD_SM if show_values else 0.0)
        text_needed = name_width + value_width
        scale = 1.0
        if text_needed > 0 and text_room < text_needed:
            scale = max(text_room, 0.2) / text_needed
        if scale < 1.0:
            for mob in (*name_mobs, *value_mobs):
                mob.scale(scale)
            name_width *= scale
            value_width *= scale

        # Guard it, following the precedent of the constructor's inline check:
        # a legend too narrow for its own names is refused rather than drawn
        # illegibly, and the message names both constants and both ways out.
        #
        # The test is the TYPE SIZE — the role's fraction times the factor
        # applied above — and deliberately NOT `typography.measure`, which is a
        # bounding box. A bounding box depends on which glyphs are in the
        # string, not on how big the type is: "sources", "runs" and "errors"
        # have no ascender, descender or capital between them, so they measure
        # their x-height, 0.0174 at this role, and tripped this guard at scale
        # 1.0 in a legend with four units to spare. The message then advised
        # widening a legend that was already wide enough, and none of its
        # escapes could work. `measure`'s own docstring says the box "errs
        # toward passing borderline text" — true for a string with descenders,
        # false for an x-height-only one, which is what this walked into.
        # Scale is what legibility actually turns on, so scale is what is
        # checked, and the guard can now only fire when something really was
        # shrunk.
        if strict_legend:
            typed_share = typography.fraction(LEGEND_ROLE) * scale
            if typed_share < typography.MIN_READABLE:
                raise typography.UnreadableTextError(
                    f"legend_width={legend_width:.3g} is too narrow for these "
                    f"names at frame_width={frame_width:.3g}: the legend is "
                    f"scaled to {scale:.3g}, typing role {LEGEND_ROLE!r} at "
                    f"{typed_share:.4f} of frame height, below "
                    f"typography.MIN_READABLE={typography.MIN_READABLE}. The "
                    f"row needs {name_left + text_needed + theme.PAD_SM:.3g} "
                    f"units and has {legend_width:.3g}. Either widen "
                    "legend_width (legend_side='below' gives the legend the "
                    "bar's full width), shorten the segment names, or type the "
                    "bar for a tighter shot with a smaller frame_width. Pass "
                    "strict_legend=False to draw it anyway."
                )

        rows = VGroup()
        for i, name_mob in enumerate(name_mobs):
            chip = Rectangle(
                width=swatch,
                height=swatch,
                fill_color=self.colors[i % len(self.colors)],
                fill_opacity=1.0,
                stroke_width=0,
            )
            chip.move_to(np.array([swatch / 2.0, 0.0, 0.0]))

            value_mob = value_mobs[i] if show_values else None

            # Fixed origin, exactly as in checks.py: the swatch starts the row,
            # the name sits at a constant offset, the value is right-aligned in
            # the reserved column. Names of different lengths therefore cannot
            # ragged-edge the numbers.
            name_mob.set_y(0.0)
            name_mob.shift(RIGHT * (name_left - name_mob.get_left()[0]))
            parts = [chip, name_mob]
            if value_mob is not None:
                value_mob.set_y(0.0)
                right_edge = max(
                    legend_width, name_left + name_width + theme.PAD_SM + value_width
                )
                value_mob.shift(RIGHT * (right_edge - value_mob.get_right()[0]))
                parts.append(value_mob)
            rows.add(VGroup(*parts))

        rows.arrange(DOWN, buff=theme.PAD_XS, aligned_edge=LEFT)
        if legend_side == "below":
            # The legend sits under the bar and shares its left edge, so a
            # legend as wide as the bar costs nothing horizontally. That is the
            # only way these names stay at full size in a half-frame station
            # bay: beside the bar they have ~0.6 units and need ~2.1.
            rows.next_to(
                np.array([0.0, -self.thickness / 2.0, 0.0]), DOWN, buff=theme.PAD_SM
            )
            rows.shift(RIGHT * (0.0 - rows.get_left()[0]))
        else:
            rows.next_to(
                np.array([length, 0.0, 0.0]), RIGHT, buff=theme.PAD_MD
            )
        self.legend = rows
        self.label_groups = list(rows)
        self.add(rows)

    def _build_inline(
        self, widths: Sequence[float], show_values: bool, frame_width: float
    ) -> None:
        group = VGroup()
        # A label is allowed to be WIDER than its own segment rather than be
        # shrunk under the readability floor. Measured on the prefill bar of
        # chatgpt_request_lifecycle: "new tail  37" fitted to 94% of a segment
        # 14% of the bar wide came out at 0.008 of frame height, against
        # typography.MIN_READABLE of 0.020 — drawn, and unreadable, which is the
        # same failure as dropping it with extra steps. Nothing about a segment
        # says the words underneath it may not overhang it; what matters is that
        # they do not overhang each OTHER, which the cursor below enforces.
        floor_height = typography.MIN_READABLE * typography.frame_height(frame_width)
        prev_right: float | None = None
        for i, name in enumerate(self.names):
            segment = self.segments[i]
            if self.drawn_fractions[i] < INLINE_MIN_FRACTION:
                # Deliberately nothing: see INLINE_MIN_FRACTION. The empty group
                # keeps `label_groups` parallel to `segments`.
                self.label_groups.append(VGroup())
                continue
            text = name if not show_values else f"{name}  {self._value_text(i)}"
            mob = typography.text(
                "micro", text, frame_width=frame_width, color=theme.FG_MUTED
            )
            # The width this string may not be squeezed below: whatever it
            # measures once scaled to exactly MIN_READABLE.
            readable_width = float(mob.width) * min(
                1.0, floor_height / float(mob.height)
            )
            utils.fit_text(mob, max(widths[i] * 0.94, readable_width, 0.2))
            mob.next_to(segment, DOWN, buff=theme.PAD_XS)
            if prev_right is not None and mob.get_left()[0] < prev_right + theme.PAD_XS:
                # An overhanging label is pushed clear of the previous one
                # rather than shrunk into it — labels run left to right, so the
                # room to give is always to the right.
                mob.shift(
                    RIGHT * (prev_right + theme.PAD_XS - float(mob.get_left()[0]))
                )
            prev_right = float(mob.get_right()[0])
            holder = VGroup(mob)
            group.add(holder)
            self.label_groups.append(holder)
        if len(group):
            self.add(group)

    # --------------------------------------------------------------- states
    def segment_for(self, name: str) -> Rectangle | None:
        for candidate, rect in zip(self.names, self.segments):
            if candidate == name:
                return rect
        return None

    def index_for(self, name: str) -> int | None:
        for i, candidate in enumerate(self.names):
            if candidate == name:
                return i
        return None

    def emphasise(self, name: str, *, dim_others: float = 0.35) -> "SegmentedBar":
        """Hold one segment at full strength and dim the rest.

        Only touches segments currently revealed by :meth:`set_shown`, so a
        growing bar can be emphasised mid-growth without the hidden tail
        flashing back into view.
        """
        chosen = self.index_for(name)
        if chosen is None:
            raise KeyError(
                f"no segment named {name!r}. Segments: {', '.join(self.names)}"
            )
        for i, rect in enumerate(self.segments):
            if i >= self._shown:
                continue
            level = 1.0 if i == chosen else dim_others
            rect.set_fill(opacity=level)
            self.label_groups[i].set_opacity(level)
        return self

    def set_shown(self, n: int) -> "SegmentedBar":
        """Reveal the first ``n`` segments and hide the rest.

        Opacity only — the submobject list never changes — so the choreography
        can grow the bar a segment at a time with ``bar.animate.set_shown(k)``.
        """
        n = max(0, min(int(n), len(self.segments)))
        self._shown = n
        for i, rect in enumerate(self.segments):
            visible = 1.0 if i < n else 0.0
            rect.set_fill(opacity=visible)
            self.label_groups[i].set_opacity(visible)
        return self

    def reset_emphasis(self) -> "SegmentedBar":
        for i, rect in enumerate(self.segments):
            level = 1.0 if i < self._shown else 0.0
            rect.set_fill(opacity=level)
            self.label_groups[i].set_opacity(level)
        return self

    def __len__(self) -> int:
        return len(self.segments)

    def __getitem__(self, index):  # type: ignore[override]
        return self.segments[index]


__all__ = ["SegmentedBar", "INLINE_MIN_FRACTION", "LABEL_MODES", "LEGEND_SIDES",
           "DEFAULT_FRAME_WIDTH"]
