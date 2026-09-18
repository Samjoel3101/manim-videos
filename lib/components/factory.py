"""Factory-tour primitives: stations, enclosures and the rails between them.

The "factory" framing — a payload entering at one end, being transformed at a
series of labelled stations, and leaving at the other — is the backbone of any
continuous-shot explainer, not just LLM ones. A request through a web stack, a
commit through CI, a photon through a telescope: same shapes.

The set is built once and never torn down; the camera moves instead (see
``lib/camera.py``). That is why these classes expose stable anchor points
(``entry``, ``exit``, ``slot``) — the choreography needs to address places that
do not move.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Mobject,
    Triangle,
    VGroup,
    VMobject,
)

from lib import theme, utils


class Station(VGroup):
    """One labelled bay in the factory, with a slot for whatever it is showing.

    Parameters
    ----------
    title:
        Shown inside the bay, sized for the zoomed-in view.
    icon:
        Optional vendored icon name (see ``lib.components.glyph``), drawn beside
        the title. Strongly preferred over a bare labelled box.
    marquee:
        Optional large label *below* the bay, invisible until
        :meth:`reveal_marquee`. It exists so the final pulled-back shot stays
        readable when the in-bay title has shrunk to a few pixels. It sits below
        rather than above so it cannot collide with an enclosing
        :class:`PipelineBox` title, and it is clamped to the bay width so
        neighbouring stations' marquees cannot overlap each other.
    """

    def __init__(
        self,
        title: str,
        *,
        subtitle: str | None = None,
        width: float = 6.6,
        height: float = 5.4,
        accent=None,
        icon: str | None = None,
        marquee: str | None = None,
        marquee_scale: float = 2.6,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.accent = accent or theme.ATTENTION
        self.bay_width = width
        self.bay_height = height

        self.bay = utils.panel(
            width=width,
            height=height,
            fill=theme.BG_ELEVATED,
            stroke=self.accent,
            stroke_width=theme.STROKE_NORMAL,
        )

        self.title_mob = utils._text(title, theme.SIZE_LABEL, theme.FG, theme.FONT_BODY)
        utils.fit_text(self.title_mob, width - 2 * theme.PAD_MD)

        # An icon beside the title says what the station *is* before the viewer
        # has read the word. The pair is centred as one header row.
        self.icon = None
        if icon:
            from lib.components.glyph import Glyph

            self.icon = Glyph(
                icon, color=self.accent, height=self.title_mob.height * 1.7
            )
            header = VGroup(self.icon, self.title_mob).arrange(
                RIGHT, buff=theme.PAD_SM
            )
        else:
            header = VGroup(self.title_mob)
        self.header = header
        header.next_to(self.bay.get_top(), DOWN, buff=theme.PAD_MD)

        self.add(self.bay, header)

        self.subtitle_mob = None
        if subtitle:
            self.subtitle_mob = utils._text(
                subtitle, theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_MONO
            )
            self.subtitle_mob.next_to(self.header, DOWN, buff=theme.PAD_XS)
            self.add(self.subtitle_mob)

        self.content = VGroup()
        self.add(self.content)

        self.marquee = None
        if marquee:
            self.marquee = utils._text(
                marquee, theme.SIZE_HEADING, self.accent, theme.FONT_BODY
            )
            self.marquee.scale(marquee_scale)
            utils.fit_text(self.marquee, width * 0.95)
            self.marquee.next_to(self.bay, DOWN, buff=theme.PAD_MD)
            self.marquee.set_opacity(0.0)
            self.add(self.marquee)

    # ------------------------------------------------------------- geometry
    @property
    def slot_size(self) -> tuple[float, float]:
        """Usable (width, height) inside the bay, below the title."""
        header = (self.bay.get_top()[1] - self._slot_top())
        return (
            self.bay_width - 2 * theme.PAD_MD,
            self.bay_height - header - theme.PAD_MD,
        )

    def _slot_top(self) -> float:
        anchor = self.subtitle_mob or self.header
        return anchor.get_bottom()[1] - theme.PAD_SM

    @property
    def slot_center(self) -> np.ndarray:
        top = self._slot_top()
        bottom = self.bay.get_bottom()[1] + theme.PAD_MD
        return np.array([self.bay.get_center()[0], (top + bottom) / 2, 0.0])

    @property
    def entry(self) -> np.ndarray:
        return self.bay.get_left()

    @property
    def exit(self) -> np.ndarray:
        return self.bay.get_right()

    # -------------------------------------------------------------- content
    def fit(self, mobject: Mobject, *, margin: float = 0.92) -> Mobject:
        """Scale ``mobject`` down to fit the slot and centre it there.

        Components in ``lib/components`` are sized for a full 14-unit frame; a
        station bay is roughly half that, so everything needs fitting. Never
        scales up — an under-sized visual is better than a blurry stretched one.
        """
        w, h = self.slot_size
        if mobject.width > 0 and mobject.height > 0:
            factor = min(w * margin / mobject.width, h * margin / mobject.height, 1.0)
            if factor < 1.0:
                mobject.scale(factor)
        mobject.move_to(self.slot_center)
        return mobject

    def load(self, mobject: Mobject) -> Mobject:
        """Fit ``mobject`` into the slot and adopt it as this station's content."""
        self.fit(mobject)
        self.content.add(mobject)
        return mobject

    def clear_content(self) -> "Station":
        self.content.remove(*self.content.submobjects)
        return self

    # --------------------------------------------------------------- states
    def activate(self, color=None) -> "Station":
        """Light the bay up — the station the camera is currently on."""
        self.bay.set_stroke(color or self.accent, width=theme.STROKE_THICK)
        self.bay.set_fill(theme.SURFACE, opacity=1.0)
        return self

    def deactivate(self) -> "Station":
        self.bay.set_stroke(self.accent, width=theme.STROKE_NORMAL)
        self.bay.set_fill(theme.BG_ELEVATED, opacity=1.0)
        return self

    def reveal_marquee(self, opacity: float = 1.0) -> "Station":
        if self.marquee is not None:
            self.marquee.set_opacity(opacity)
        return self


class PipelineBox(VGroup):
    """A labelled enclosure grouping several stations into one machine.

    Used for the "this whole thing is the LLM" beat: the viewer needs to see
    that tokenizer, embedder, transformer and sampler live inside one box.

    ``pad`` does double duty: it is the visual breathing room around the
    contents, and it is what lifts the box title clear of a tight shot framed on
    one enclosed station. Shrink it and the title starts hanging into close-ups.
    """

    def __init__(
        self,
        contents: Sequence[Mobject],
        *,
        title: str,
        subtitle: str | None = None,
        pad: float = 2.2,
        accent=None,
        title_scale: float = 1.8,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if not contents:
            raise ValueError("PipelineBox needs at least one enclosed mobject")

        self.accent = accent or theme.ASSISTANT
        inner = VGroup(*contents)

        self.frame = utils.panel(
            width=inner.width + 2 * pad,
            height=inner.height + 2 * pad + 0.8,
            fill=theme.BG,
            stroke=self.accent,
            stroke_width=theme.STROKE_NORMAL,
            radius=theme.CORNER_RADIUS * 2,
        )
        self.frame.move_to(inner.get_center() + UP * 0.4)

        # Big enough to read in the pulled-back shot, and kept high enough above
        # the enclosed stations that it stays out of frame during a tight shot
        # on any one of them — that is what `pad` is buying.
        self.title_mob = utils._text(title, theme.SIZE_HEADING, self.accent, theme.FONT_BODY)
        self.title_mob.scale(title_scale)
        self.title_mob.next_to(self.frame.get_top(), DOWN, buff=theme.PAD_SM)

        self.add(self.frame, self.title_mob)

        self.subtitle_mob = None
        if subtitle:
            self.subtitle_mob = utils._text(
                subtitle, theme.SIZE_LABEL, theme.FG_MUTED, theme.FONT_MONO
            )
            self.subtitle_mob.scale(title_scale * 0.7)
            self.subtitle_mob.next_to(self.title_mob, DOWN, buff=theme.PAD_SM)
            self.add(self.subtitle_mob)

    @property
    def entry(self) -> np.ndarray:
        return self.frame.get_left()

    @property
    def exit(self) -> np.ndarray:
        return self.frame.get_right()


class Conveyor(VGroup):
    """A rail joining a sequence of world-space points.

    Exposes ``path``, a single ``VMobject`` suitable for ``MoveAlongPath`` — so
    one payload can traverse several corners in one continuous animation rather
    than a chain of separate moves.
    """

    def __init__(
        self,
        points: Sequence,
        *,
        color=None,
        stroke_width: float | None = None,
        chevrons: int = 0,
        chevron_size: float = 0.22,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        pts = [np.array(p, dtype=float) for p in points]
        if len(pts) < 2:
            raise ValueError("Conveyor needs at least two points")

        self.color_ = color or theme.FG_FAINT
        self.path = VMobject(
            stroke_color=self.color_,
            stroke_width=theme.STROKE_NORMAL if stroke_width is None else stroke_width,
        )
        self.path.set_points_as_corners(pts)
        self.add(self.path)

        self.chevrons = VGroup()
        for i in range(chevrons):
            alpha = (i + 1) / (chevrons + 1)
            point = self.path.point_from_proportion(alpha)
            ahead = self.path.point_from_proportion(min(1.0, alpha + 1e-3))
            direction = ahead - point
            angle = float(np.arctan2(direction[1], direction[0]))
            mark = Triangle(
                fill_color=self.color_, fill_opacity=1.0, stroke_width=0
            ).scale(chevron_size)
            mark.rotate(angle - np.pi / 2).move_to(point)
            self.chevrons.add(mark)
        if chevrons:
            self.add(self.chevrons)

    @property
    def start(self) -> np.ndarray:
        return self.path.get_start()

    @property
    def end(self) -> np.ndarray:
        return self.path.get_end()

    def point_at(self, alpha: float) -> np.ndarray:
        """World position a fraction ``alpha`` along the rail."""
        return self.path.point_from_proportion(min(1.0, max(0.0, alpha)))


def rail_between(a: Mobject, b: Mobject, *, gap: float = theme.PAD_MD, **kwargs) -> Conveyor:
    """Straight conveyor from the right edge of ``a`` to the left edge of ``b``."""
    return Conveyor(
        [a.get_right() + RIGHT * gap, b.get_left() + LEFT * gap], **kwargs
    )


__all__ = ["Station", "PipelineBox", "Conveyor", "rail_between"]
