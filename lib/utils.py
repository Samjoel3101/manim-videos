"""Small helpers shared by components and scenes.

Nothing here draws a domain concept — that belongs in ``lib/components``.
This module is for layout, text construction and frame-safety plumbing that
would otherwise be copy-pasted into every component.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Mobject,
    RoundedRectangle,
    Text,
    VGroup,
    config,
)

from lib import theme


def body(text: str, **kwargs) -> Text:
    """Themed body text. Prefer this over bare ``Text`` so fonts stay consistent."""
    return _text(text, theme.SIZE_BODY, theme.FG, theme.FONT_BODY, **kwargs)


def label(text: str, **kwargs) -> Text:
    """Small muted label, e.g. an axis name or a caption under a diagram."""
    return _text(text, theme.SIZE_LABEL, theme.FG_MUTED, theme.FONT_BODY, **kwargs)


def heading(text: str, **kwargs) -> Text:
    return _text(text, theme.SIZE_HEADING, theme.FG, theme.FONT_BODY, **kwargs)


def mono(text: str, **kwargs) -> Text:
    """Monospaced text — token strings, ids, code, anything character-aligned."""
    return _text(text, theme.SIZE_LABEL, theme.FG, theme.FONT_MONO, **kwargs)


def _text(text: str, size: float, color, font: str | None, **kwargs) -> Text:
    kwargs.setdefault("font_size", size)
    kwargs.setdefault("color", color)
    if font is not None:
        kwargs.setdefault("font", font)
    return Text(text, **kwargs)


def panel(
    width: float,
    height: float,
    *,
    fill=theme.BG_ELEVATED,
    stroke=theme.BORDER,
    radius: float | None = None,
    fill_opacity: float = 1.0,
    stroke_width: float | None = None,
) -> RoundedRectangle:
    """A themed rounded container — the base shape for cards, chips and windows."""
    return RoundedRectangle(
        width=width,
        height=height,
        corner_radius=theme.CORNER_RADIUS if radius is None else radius,
        fill_color=fill,
        fill_opacity=fill_opacity,
        stroke_color=stroke,
        stroke_width=theme.STROKE_HAIRLINE if stroke_width is None else stroke_width,
    )


def fit_text(text: Text, max_width: float) -> Text:
    """Scale ``text`` down in place if it is wider than ``max_width``. Never up."""
    if text.width > max_width and text.width > 0:
        text.scale(max_width / text.width)
    return text


def stack(
    mobjects: Iterable[Mobject], *, gap: float = theme.PAD_SM, direction=DOWN, align=LEFT
) -> VGroup:
    """Arrange ``mobjects`` in a line with themed spacing. Returns a VGroup."""
    group = VGroup(*mobjects)
    if len(group) > 1:
        group.arrange(direction, buff=gap, aligned_edge=align)
    return group


def wrap_words(words: Sequence[str], per_line: int) -> list[list[str]]:
    """Chunk ``words`` into rows of at most ``per_line`` — used for token strips."""
    if per_line < 1:
        raise ValueError("per_line must be >= 1")
    return [list(words[i : i + per_line]) for i in range(0, len(words), per_line)]


def frame_bounds() -> tuple[float, float]:
    """(width, height) of the render frame, honouring the active config."""
    return config.frame_width, config.frame_height


def is_in_frame(mobject: Mobject, margin: float = theme.SAFE_MARGIN) -> bool:
    """True if ``mobject`` sits inside the safe area. Used by the visual tests."""
    fw, fh = frame_bounds()
    left, right = -fw / 2 + margin, fw / 2 - margin
    bottom, top = -fh / 2 + margin, fh / 2 - margin
    return (
        mobject.get_left()[0] >= left - 1e-6
        and mobject.get_right()[0] <= right + 1e-6
        and mobject.get_bottom()[1] >= bottom - 1e-6
        and mobject.get_top()[1] <= top + 1e-6
    )


def pin(mobject: Mobject, edge=UP, margin: float = theme.PAD_XL) -> Mobject:
    """Move ``mobject`` to a frame edge with themed margin."""
    return mobject.to_edge(edge, buff=margin)


__all__ = [
    "body",
    "label",
    "heading",
    "mono",
    "panel",
    "fit_text",
    "stack",
    "wrap_words",
    "frame_bounds",
    "is_in_frame",
    "pin",
]
