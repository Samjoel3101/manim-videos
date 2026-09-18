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

from lib import theme, typography, utils


#: Largest share of a wide bay's width a left-hand header may take. The rest is
#: the slot, which a close-up needs for its content.
#:
#: Kept well under half deliberately. The bay's *content* is the subject of a
#: close-up — the chips, the vectors, the chart — and the header only has to
#: name what is doing the work. An earlier 0.58 left the slot barely 2.5 units
#: wide inside a 9.6 bay, so five vector columns rendered as illegible confetti
#: beside a title three times their size.
HEADER_SHARE = 0.36


class Station(VGroup):
    """One labelled bay in the factory, with a slot for whatever it is showing.

    Parameters
    ----------
    title:
        Shown inside the bay, sized for the zoomed-in view.
    icon:
        Optional vendored icon name (see ``lib.components.glyph``), drawn beside
        the title. Strongly preferred over a bare labelled box.
    wide_label:
        Text naming this bay at the pull-back, drawn inside it with the icon and
        sized for ``wide_width``. Preferred over ``marquee`` for a tight layout:
        it fills the bay instead of crowding the space beside it.
    marquee_side:
        Which side of the bay the marquee sits on: ``"up"``, ``"down"``,
        ``"left"`` or ``"right"``. A vertical column wants ``"left"`` or
        ``"right"``, which both keeps the stack short and puts the side margin
        a 16:9 frame leaves empty to use.
    marquee:
        Optional large label beside the bay, invisible until
        :meth:`reveal_marquee`. It exists so the final pulled-back shot stays
        readable when the in-bay title has shrunk to a few pixels. It sits below
        rather than above so it cannot collide with an enclosing
        :class:`PipelineBox` title, and it is clamped to the bay width so
        neighbouring stations' marquees cannot overlap each other.
    wide_label:
        Text naming this bay at the pull-back, drawn *inside* it alongside the
        icon and sized for ``wide_width``. Preferred over ``marquee`` in a tight
        layout: it fills the bay rather than crowding the space beside it, and
        an empty lit rectangle at the wide shot reads as a UI mockup rather than
        a machine.
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
        header_side: str = "top",
        wide_label: str | None = None,
        marquee: str | None = None,
        marquee_side: str = "down",
        marquee_role: str = "display",
        marquee_max_width: float | None = None,
        shot_width: float = 12.0,
        wide_width: float = 25.0,
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

        # Sized for the shot it will be read in, not in absolute points — see
        # lib/typography.py. `shot_width` is the close-up this bay gets;
        # `wide_width` is the final pull-back the marquee has to survive.
        self.shot_width = shot_width
        self.wide_width = wide_width
        # Bold: a bay title has to survive the pull-back, where thin stems
        # antialias into grey against a dark bay long before the glyph gets too
        # small to recognise. Weight buys contrast that size alone does not.
        self.title_mob = typography.text(
            "heading", title, frame_width=shot_width, color=theme.FG, bold=True
        )
        utils.fit_text(self.title_mob, width - 2 * theme.PAD_MD)

        self.subtitle_mob = None
        if subtitle:
            self.subtitle_mob = typography.text(
                "caption", subtitle, frame_width=shot_width,
                color=theme.FG_MUTED, mono=True,
            )

        # An icon beside the title says what the station *is* before the viewer
        # has read the word.
        self.icon = None
        if icon:
            from lib.components.glyph import Glyph

            self.icon = Glyph(
                icon, color=self.accent, height=self.title_mob.height * 1.7
            )

        if header_side not in ("top", "left"):
            raise ValueError("header_side must be 'top' or 'left'")
        self.header_side = header_side

        words = VGroup(self.title_mob)
        if self.subtitle_mob is not None:
            words.add(self.subtitle_mob)

        if header_side == "top":
            words.arrange(DOWN, buff=theme.PAD_XS)
            header = (
                VGroup(self.icon, words).arrange(RIGHT, buff=theme.PAD_SM)
                if self.icon is not None
                else VGroup(words)
            )
            header.next_to(self.bay.get_top(), DOWN, buff=theme.PAD_MD)
        else:
            # A wide, short bay has no vertical room for a stacked header, so
            # the naming sits in a left-hand block and the slot takes the rest.
            words.arrange(DOWN, buff=theme.PAD_XS, aligned_edge=LEFT)
            header = (
                VGroup(self.icon, words).arrange(RIGHT, buff=theme.PAD_SM)
                if self.icon is not None
                else VGroup(words)
            )
            # Cap the header's share of the bay before placing it. Clamping to
            # the full bay width stops it overflowing but leaves the slot with
            # nothing, so a close-up has nowhere to put its content.
            limit = width * HEADER_SHARE
            if header.width > limit:
                header.scale(limit / header.width)
            header.move_to(self.bay.get_left() + RIGHT * (header.width / 2 + theme.PAD_MD))

        self.header = header
        #: The header's fading parts, split by how they carry colour: text is
        #: filled, an icon is stroked. See :meth:`_fade_parts`.
        self.header_words = words
        self.header_icon = self.icon
        self.add(self.bay, header)

        self.content = VGroup()
        self.add(self.content)

        # The wide-shot identity of this bay. At the pull-back the close-up
        # header is a couple of pixels tall, and an empty lit rectangle reads as
        # a UI mockup rather than a machine — so the bay names itself, inside,
        # at a size meant for that shot. Hidden until the pull-back reveals it.
        self.wide_label = None
        self.wide_label_words = None
        self.wide_label_icon = None
        if wide_label:
            from lib.components.glyph import Glyph

            label_words = typography.text(
                "heading", wide_label, frame_width=wide_width,
                color=self.accent, bold=True,
            )
            label_icon = (
                Glyph(icon, color=self.accent, height=label_words.height * 1.25)
                if icon
                else None
            )
            parts = [label_words] if label_icon is None else [label_icon, label_words]
            label = VGroup(*parts).arrange(RIGHT, buff=theme.PAD_MD)
            factor = min(
                (width * 0.82) / label.width, (height * 0.62) / label.height, 1.0
            )
            if factor < 1.0:
                label.scale(factor)
            label.move_to(self.bay.get_center())
            self.wide_label = label
            self.wide_label_words = label_words
            self.wide_label_icon = label_icon
            # Hidden the same way it will later be shown — on fill for text and
            # stroke for the icon — because a blanket set_opacity would fill the
            # icon's outlines in and it would come back as a solid blob.
            self.set_wide_opacity(0.0)
            self.add(label)

        self.marquee = None
        if marquee:
            self.marquee = typography.text(
                marquee_role, marquee, frame_width=wide_width,
                color=self.accent, bold=True,
            )
            # Above or below, the bay's own width is the natural clamp. Beside
            # it, there is no such bound, so the caller states one — that side
            # margin is exactly the space a tall column has to spend.
            limit = (
                marquee_max_width
                if marquee_max_width is not None
                else width * 0.95
            )
            utils.fit_text(self.marquee, limit)
            sides = {"up": UP, "down": DOWN, "left": LEFT, "right": RIGHT}
            if marquee_side not in sides:
                raise ValueError(f"marquee_side must be one of {sorted(sides)}")
            self.marquee_side = marquee_side
            self.marquee.next_to(self.bay, sides[marquee_side], buff=theme.PAD_MD)
            self.marquee.set_opacity(0.0)
            self.add(self.marquee)

    # ------------------------------------------------------------- geometry
    @property
    def slot_size(self) -> tuple[float, float]:
        """Usable (width, height) inside the bay, clear of the header."""
        if self.header_side == "left":
            used = self.header.width + 2 * theme.PAD_MD
            return (
                self.bay_width - used - theme.PAD_MD,
                self.bay_height - 2 * theme.PAD_SM,
            )
        consumed = self.bay.get_top()[1] - self._slot_top()
        return (
            self.bay_width - 2 * theme.PAD_MD,
            self.bay_height - consumed - theme.PAD_MD,
        )

    def _slot_top(self) -> float:
        return self.header.get_bottom()[1] - theme.PAD_SM

    @property
    def slot_center(self) -> np.ndarray:
        if self.header_side == "left":
            left = self.header.get_right()[0] + theme.PAD_MD
            right = self.bay.get_right()[0] - theme.PAD_MD
            return np.array(
                [(left + right) / 2, self.bay.get_center()[1], 0.0]
            )
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

    # ------------------------------------------------------- label cross-fade
    @staticmethod
    def _fade_parts(words, icon, opacity: float) -> list:
        """Animations fading a text+icon pair, each on the channel it uses.

        Text carries its colour in the fill; a Lucide icon carries it in the
        stroke with the fill deliberately cleared. Fading both with a blanket
        ``set_opacity`` raises the icon's fill too and it renders as a solid
        blob — the same class of bug as lighting a glow halo by fill rather
        than stroke, and just as invisible until someone looks at a frame.
        """
        anims = []
        if words is not None:
            anims.append(words.animate.set_fill(opacity=opacity))
        if icon is not None:
            anims.append(icon.animate.fade_to_opacity(opacity))
        return anims

    def set_wide_opacity(self, opacity: float) -> "Station":
        """Show or hide the wide-shot label immediately, without animating."""
        if self.wide_label_words is not None:
            self.wide_label_words.set_fill(opacity=opacity)
        if self.wide_label_icon is not None:
            self.wide_label_icon.fade_to_opacity(opacity)
        return self

    def reveal_wide(self, opacity: float = 1.0) -> list:
        """Animations swapping the close-up header for the wide-shot label.

        They occupy the same bay, so this is a cross-fade, not two reveals. The
        close-up header is a couple of pixels tall at the pull-back and only
        muddies the name that replaces it.
        """
        if self.wide_label is None:
            return []
        # The label may have been re-parented out of this group by the set (see
        # FactorySet), so address it directly rather than through the station.
        anims = self._fade_parts(self.wide_label_words, self.wide_label_icon, opacity)
        anims += self._fade_parts(
            self.header_words, self.header_icon, 1.0 - opacity
        )
        if self.content is not None and len(self.content):
            anims.append(self.content.animate.set_opacity(1.0 - opacity))
        return anims

    def reveal_marquee(self, opacity: float = 1.0) -> "Station":
        if self.marquee is not None:
            self.marquee.set_opacity(opacity)
        return self


class PipelineBox(VGroup):
    """A labelled enclosure grouping several stations into one machine.

    Used for the "this whole thing is the LLM" beat: the viewer needs to see
    that tokenizer, embedder, transformer and sampler live inside one box.

    The title sits above the frame, not inside it, so it cannot collide with
    anything the enclosed contents place near their own top edge. ``pad`` is
    then purely visual breathing room around the contents.
    """

    def __init__(
        self,
        contents: Sequence[Mobject],
        *,
        title: str,
        subtitle: str | None = None,
        pad: float = 2.2,
        accent=None,
        title_role: str = "title",
        wide_width: float = 25.0,
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

        # Sized for the pulled-back shot, since that is where it is read, and
        # placed *outside* the frame rather than inside it. Inside, it competes
        # for space with whatever the enclosed stations put near their top edge
        # — station marquees, in this repo's case — and the collision is only
        # visible at the one shot where both are on screen.
        self.title_mob = typography.text(
            title_role, title, frame_width=wide_width, color=self.accent, bold=True
        )
        self.subtitle_mob = None
        if subtitle:
            self.subtitle_mob = typography.text(
                "caption", subtitle, frame_width=wide_width,
                color=theme.FG_MUTED, mono=True,
            )

        # Title above subtitle, the pair stacked above the frame.
        header = VGroup(self.title_mob)
        if self.subtitle_mob is not None:
            header.add(self.subtitle_mob)
            header.arrange(DOWN, buff=theme.PAD_XS)
        # Clamp to the box: a caption wider than the thing it names reads as a
        # banner across the whole frame and collides with whatever sits above.
        if header.width > self.frame.width:
            header.scale(self.frame.width / header.width)
        header.next_to(self.frame.get_top(), UP, buff=theme.PAD_SM)
        self.caption = header
        self.add(self.frame, header)

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
