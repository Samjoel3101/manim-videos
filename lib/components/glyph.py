"""Vector icons.

A labelled rectangle says "a thing"; an icon says *which* thing, before the
viewer has read anything. This is the single highest-value visual upgrade
available to a diagram-style explainer, and it costs one SVG import.

Icons are vendored in ``lib/assets/icons`` (Lucide, ISC licence) rather than
fetched at render time, so a render is reproducible offline and a pinned icon
set cannot change under an old video.
"""

from __future__ import annotations

import functools
import pathlib
from typing import Iterable

from manim import Dot, SVGMobject, VGroup, VMobject

from lib import theme

ICON_DIR = pathlib.Path(__file__).resolve().parents[1] / "assets" / "icons"

#: Sub-paths shorter than this (in SVG user units) are Lucide's "indicator dot"
#: idiom: a zero-length line with a round cap. Manim renders those as nothing,
#: so they are replaced with a real filled dot. Without this, the server icon
#: silently loses its status lights and nobody notices until the render.
DEGENERATE_LENGTH = 0.06


@functools.lru_cache(maxsize=1)
def available_icons() -> tuple[str, ...]:
    """Names of every vendored icon, without the extension."""
    return tuple(sorted(p.stem for p in ICON_DIR.glob("*.svg")))


def icon_path(name: str) -> pathlib.Path:
    path = ICON_DIR / f"{name}.svg"
    if not path.exists():
        raise FileNotFoundError(
            f"no vendored icon named {name!r}. Available: {', '.join(available_icons())}. "
            f"Add one by dropping a Lucide SVG into {ICON_DIR.relative_to(ICON_DIR.parents[2])}."
        )
    return path


class Glyph(VGroup):
    """A vector icon, themed and sized for a slot.

    Lucide icons are *stroked*, not filled, so the fill is cleared and the
    stroke carries the colour. Setting a blanket fill opacity on the import is
    what makes icons look hollow and wrong.
    """

    def __init__(
        self,
        name: str,
        *,
        color=None,
        height: float = 1.0,
        stroke_width: float = 3.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.icon_name = name
        self.accent = color or theme.FG

        svg = SVGMobject(str(icon_path(name)))
        parts = VGroup()
        for sub in svg.submobjects:
            parts.add(self._restore_dot(sub, stroke_width))

        parts.set_fill(opacity=0)
        parts.set_stroke(color=self.accent, width=stroke_width)
        # The replacement dots are filled, not stroked, so re-assert them after
        # the blanket stroke pass above.
        for sub in parts:
            if getattr(sub, "_is_indicator_dot", False):
                sub.set_fill(self.accent, opacity=1).set_stroke(width=0)

        parts.scale_to_fit_height(height)
        self.parts = parts
        self.add(parts)

    @staticmethod
    def _restore_dot(sub: VMobject, stroke_width: float) -> VMobject:
        """Swap a degenerate zero-length path for a dot Manim can actually draw."""
        if max(sub.width, sub.height) > DEGENERATE_LENGTH:
            return sub
        dot = Dot(radius=max(sub.width, sub.height, 0.02) * 1.6 + stroke_width * 0.01)
        dot.move_to(sub.get_center())
        dot._is_indicator_dot = True
        return dot

    def recolor(self, color) -> "Glyph":
        self.accent = color
        for sub in self.parts:
            if getattr(sub, "_is_indicator_dot", False):
                sub.set_fill(color, opacity=1)
            else:
                sub.set_stroke(color=color)
        return self


class IconTile(VGroup):
    """An icon inside a rounded tile — the standard node in a factory diagram.

    This is what replaces a labelled box. The tile carries the colour and the
    shape language; the icon carries the meaning; the caption sits outside so it
    can be styled and hidden independently of the node itself.
    """

    def __init__(
        self,
        icon: str,
        *,
        label: str | None = None,
        color=None,
        size: float = 2.2,
        icon_ratio: float = 0.45,
        corner_radius: float | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.accent = color or theme.NETWORK

        self.tile = theme_tile(size, self.accent, corner_radius)
        self.glyph = Glyph(icon, color=self.accent, height=size * icon_ratio)
        self.glyph.move_to(self.tile.get_center())
        self.add(self.tile, self.glyph)

        self.label_mob = None
        if label:
            from lib import utils

            self.label_mob = utils._text(
                label, theme.SIZE_LABEL, theme.FG_MUTED, theme.FONT_BODY
            )
            utils.fit_text(self.label_mob, size * 1.4)
            self.label_mob.next_to(self.tile, theme_down(), buff=theme.PAD_SM)
            self.add(self.label_mob)

    @property
    def entry(self):
        return self.tile.get_left()

    @property
    def exit(self):
        return self.tile.get_right()

    def recolor(self, color) -> "IconTile":
        self.accent = color
        self.tile.set_stroke(color)
        self.glyph.recolor(color)
        return self


def theme_tile(size: float, accent, corner_radius: float | None = None):
    """The tile shape, with the series' gradient fill. Shared by IconTile."""
    from manim import RoundedRectangle

    tile = RoundedRectangle(
        width=size,
        height=size,
        corner_radius=size * 0.145 if corner_radius is None else corner_radius,
        stroke_color=accent,
        stroke_width=theme.STROKE_NORMAL,
    )
    # A slight vertical gradient reads as a lit surface rather than flat paper.
    tile.set_fill(color=[theme.SURFACE, theme.BG_ELEVATED], opacity=1.0)
    return tile


def theme_down():
    from manim import DOWN

    return DOWN


__all__ = ["Glyph", "IconTile", "available_icons", "icon_path", "ICON_DIR"]
