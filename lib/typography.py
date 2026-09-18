"""The type system: text sized relative to the shot, not in absolute points.

In a video whose camera zooms, an absolute font size means nothing. A label that
reads perfectly in a close-up is illegible when the camera pulls back to three
times the width, which is exactly how this repo ended up with arbitrary `×2.6`
and `×1.8` multipliers scattered through its components.

So type is specified as a **fraction of frame height**, and the point size is
derived from the shot width it is designed for:

    frame_height = frame_width * 9 / 16
    cap_height   = fraction * frame_height
    font_size    = cap_height / CAP_HEIGHT_PER_POINT

That makes "a station title" one decision — how big should it look on screen —
instead of a different number for every shot.

Measured, not guessed: Manim's cap height is linear in font size at
0.01013 world units per point for the body face (see
`tests/test_typography.py`, which fails if a Manim upgrade changes it).
"""

from __future__ import annotations

from typing import Iterable

from manim import BOLD, MEDIUM, Text

from lib import theme

#: World units of cap height per point of ``font_size``. Empirical.
CAP_HEIGHT_PER_POINT = 0.010128

#: 16:9 everywhere. Frame height is what type is measured against, because
#: that is what stays constant as a widescreen frame gets wider.
ASPECT = 16 / 9


#: Cap height as a fraction of frame height, per role. A modular scale with a
#: ratio of roughly 1.25, anchored on HEADING — the size a station title
#: rendered at in the first cut that people said looked right.
ROLES: dict[str, float] = {
    "display": 0.082,  # the wide shot's station marquees
    "title": 0.066,    # the name of a machine, read at a distance
    "heading": 0.053,  # a station's own title, in its close-up
    "body": 0.042,     # prose the viewer actually reads
    "label": 0.034,    # captions, axis names, rail labels
    "caption": 0.027,  # subtitles under a title
    "micro": 0.022,    # token ids, dense numeric detail
}

#: Below this share of frame height, text stops being reliably readable on a
#: phone. Anything smaller is decoration, and should be treated as such.
MIN_READABLE = 0.020

#: Weights available on the body face. Hierarchy should lean on weight before
#: it reaches for another size step.
WEIGHT_NORMAL = MEDIUM
WEIGHT_BOLD = BOLD


class UnreadableTextError(ValueError):
    """Raised when a role would render below the readability floor."""


def frame_height(frame_width: float) -> float:
    return frame_width / ASPECT


def cap_height(role: str, frame_width: float) -> float:
    """World-space cap height for ``role`` at a shot ``frame_width`` wide."""
    return fraction(role) * frame_height(frame_width)


def fraction(role: str) -> float:
    try:
        return ROLES[role]
    except KeyError:
        raise KeyError(
            f"unknown type role {role!r}. Roles: {', '.join(ROLES)}"
        ) from None


def size_for(role: str, frame_width: float, *, strict: bool = True) -> float:
    """Point size so ``role`` occupies its share of the frame at this shot.

    ``strict`` raises if the role would land below :data:`MIN_READABLE`, which
    can only happen if a caller passes a role a fraction lower than the floor.
    """
    share = fraction(role)
    if strict and share < MIN_READABLE:
        raise UnreadableTextError(
            f"role {role!r} is {share:.1%} of frame height, below the "
            f"{MIN_READABLE:.1%} readability floor"
        )
    return cap_height(role, frame_width) / CAP_HEIGHT_PER_POINT


def text(
    role: str,
    string: str,
    *,
    frame_width: float,
    color=None,
    mono: bool = False,
    bold: bool = False,
    **kwargs,
) -> Text:
    """Themed text sized for the shot it will be seen in.

    ``frame_width`` is the camera width of the shot this text is designed for —
    a station title uses the tight-shot width, a wide-shot marquee uses the
    pull-back width. Getting that argument wrong is the whole bug this module
    exists to prevent, so it is required and keyword-only.
    """
    kwargs.setdefault("font_size", size_for(role, frame_width))
    kwargs.setdefault("color", color if color is not None else theme.FG)
    kwargs.setdefault("weight", WEIGHT_BOLD if bold else WEIGHT_NORMAL)
    font = theme.FONT_MONO if mono else theme.FONT_BODY
    if font is not None:
        kwargs.setdefault("font", font)
    return Text(string, **kwargs)


def measure(mobject, frame_width: float) -> float:
    """What share of frame height ``mobject`` occupies at this shot.

    Note this measures the full bounding box, including descenders, while
    :data:`ROLES` is specified in cap height. The box is always the larger of
    the two, so comparing it against :data:`MIN_READABLE` errs toward passing
    borderline text rather than failing readable text.

    The review tool for typography: render a shot, measure the labels in it,
    and anything under :data:`MIN_READABLE` is a bug.
    """
    return mobject.height / frame_height(frame_width)


def audit(items: Iterable[tuple[str, object]], frame_width: float) -> list[str]:
    """Names of items that fall below the readability floor at this shot."""
    return [
        name
        for name, mob in items
        if measure(mob, frame_width) < MIN_READABLE
    ]


__all__ = [
    "ROLES",
    "MIN_READABLE",
    "CAP_HEIGHT_PER_POINT",
    "ASPECT",
    "WEIGHT_NORMAL",
    "WEIGHT_BOLD",
    "UnreadableTextError",
    "frame_height",
    "cap_height",
    "fraction",
    "size_for",
    "text",
    "measure",
    "audit",
]
