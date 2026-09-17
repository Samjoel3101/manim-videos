"""Single source of truth for colour, type and spacing across every video.

Scenes and components MUST pull values from here rather than hardcoding hex
strings or font sizes — that is what keeps a back catalogue of videos looking
like one series. Changing a value here changes it everywhere, so treat edits as
a series-wide decision.
"""

from __future__ import annotations

from manim import ManimColor

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------
# Deep near-black background with a slightly blue cast, in the 3b1b tradition.
BG = ManimColor("#0E1117")
BG_ELEVATED = ManimColor("#161B22")  # panels/cards sitting above the background
SURFACE = ManimColor("#1F2630")  # inputs, chips, inert containers
BORDER = ManimColor("#2D3643")

# Text
FG = ManimColor("#E6EDF3")  # primary text
FG_MUTED = ManimColor("#8B97A6")  # labels, captions, de-emphasised text
FG_FAINT = ManimColor("#4A5565")  # hairlines, inactive states

# Semantic accents. Each concept keeps the same colour across every video:
# a token is always amber, an embedding is always teal, and so on.
USER = ManimColor("#4C8DFF")  # the human / client side
ASSISTANT = ManimColor("#22C99B")  # the model / server side
TOKEN = ManimColor("#F2A93B")  # discrete tokens
EMBED = ManimColor("#3FC7D4")  # continuous vectors / embeddings
ATTENTION = ManimColor("#C77DFF")  # attention, routing, mixing
PROB = ManimColor("#FF8FA3")  # probabilities and sampling
NETWORK = ManimColor("#7AA2F7")  # wires, packets, transport
WARN = ManimColor("#FFD166")
ERROR = ManimColor("#F87171")

#: Ordered palette for "n arbitrary distinguishable things" (heads, layers,
#: series). Cycle it with :func:`series_color`.
SERIES = [USER, TOKEN, EMBED, ATTENTION, ASSISTANT, PROB, NETWORK, WARN]


def series_color(i: int) -> ManimColor:
    """Colour number ``i`` from the categorical palette, wrapping around."""
    return SERIES[i % len(SERIES)]


# --------------------------------------------------------------------------
# Type
# --------------------------------------------------------------------------
# Font *candidates*, most preferred first. Resolved against what is actually
# installed at import time so a missing font degrades instead of warning on
# every single Text() call.
FONT_BODY_CANDIDATES = ("Inter", "Helvetica Neue", "DejaVu Sans")
FONT_MONO_CANDIDATES = ("JetBrains Mono", "SF Mono", "DejaVu Sans Mono")


def _resolve_font(candidates: tuple[str, ...]) -> str | None:
    """Return the first installed font from ``candidates``, else ``None``.

    ``None`` means "let Pango pick the default", which is always safe.
    """
    try:
        from manim.utils.tex import TexFontTemplates  # noqa: F401  (import guard)
    except Exception:  # pragma: no cover - only about import-time safety
        pass
    try:
        import manimpango

        installed = set(manimpango.list_fonts())
    except Exception:  # pragma: no cover - environments without pango listing
        return None
    for name in candidates:
        if name in installed:
            return name
    return None


FONT_BODY = _resolve_font(FONT_BODY_CANDIDATES)
FONT_MONO = _resolve_font(FONT_MONO_CANDIDATES)

# Type scale, in Manim font-size units (a 1080p frame is 8 units tall).
SIZE_TITLE = 48
SIZE_HEADING = 36
SIZE_BODY = 28
SIZE_LABEL = 22
SIZE_CAPTION = 18
SIZE_MICRO = 14

# --------------------------------------------------------------------------
# Spacing / geometry
# --------------------------------------------------------------------------
# One rhythm unit. All gaps are multiples of it so components composed at
# different times still line up.
UNIT = 0.25

PAD_XS = UNIT * 0.5  # 0.125
PAD_SM = UNIT  # 0.25
PAD_MD = UNIT * 2  # 0.5
PAD_LG = UNIT * 3  # 0.75
PAD_XL = UNIT * 5  # 1.25

CORNER_RADIUS = 0.12
STROKE_HAIRLINE = 1.0
STROKE_NORMAL = 2.0
STROKE_THICK = 3.5

#: Keep content inside this margin so nothing is clipped at 16:9.
SAFE_MARGIN = 0.5

# --------------------------------------------------------------------------
# Timing
# --------------------------------------------------------------------------
# Named durations, so pacing is consistent across videos and tunable in one place.
T_INSTANT = 0.2
T_FAST = 0.4
T_NORMAL = 0.7
T_SLOW = 1.2
T_BEAT = 0.5  # a held pause for the viewer to read


def apply(scene) -> None:
    """Apply the theme background to a Scene. Call first in ``construct``."""
    scene.camera.background_color = BG
