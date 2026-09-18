"""The registry of snapshot cases.

One entry per component view that should be pixel-stable. ``scripts/
approve_baselines.py`` and ``tests/test_components_snapshot.py`` both read this
list, so a case can never drift out of sync with its baseline name.

Adding a component? Add a case here and approve its baseline once you have
eyeballed the render.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from manim import Mobject, VGroup

from lib import effects, theme
from lib.components.chat_ui import ChatWindow, StreamingBubble, TypingIndicator
from lib.components.factory import Conveyor, PipelineBox, Station
from lib.components.glyph import Glyph, IconTile
from lib.components.network import RequestPath, ServerRack
from lib.components.probability import ProbabilityChart
from lib.components.tokens import TokenStrip
from lib.components.transformer import AttentionMatrix, TransformerStack
from lib.components.vectors import EmbeddingGrid, VectorColumn, stable_vector


def _chat_window() -> Mobject:
    win = ChatWindow(width=6.0, height=6.2)
    win.add_message("How do you actually work?", "user")
    win.add_message("Let me walk you through it.", "assistant")
    return win


def _token_strip() -> Mobject:
    return TokenStrip("How does ChatGPT work?", show_ids=True, per_line=3)


def _vector_column() -> Mobject:
    return VectorColumn(stable_vector("How", 12), label="How")


def _embedding_grid() -> Mobject:
    data = np.array([stable_vector(t, 8) for t in ("How", "does", "it", "work")])
    return EmbeddingGrid(data, row_labels=["How", "does", "it", "work"])


def _probability_chart() -> Mobject:
    return ProbabilityChart(
        {" The": 3.1, " It": 2.0, " Your": 1.4, " When": 0.9, " A": 0.2},
        logits=True,
        title="next token",
    )


def _glyph_row():
    """A spread of icons. Guards the SVG import and the indicator-dot repair —
    `server` and `cpu` both carry degenerate paths Manim would otherwise drop."""
    from manim import RIGHT, VGroup

    names = ("server", "cpu", "database", "message-square", "zap", "layers")
    return VGroup(
        *[Glyph(n, color=theme.series_color(i), height=1.2) for i, n in enumerate(names)]
    ).arrange(RIGHT, buff=0.6)


def _icon_tile():
    from manim import RIGHT, VGroup

    return VGroup(
        IconTile("message-square", label="client", color=theme.USER),
        IconTile("server", label="web server", color=theme.NETWORK),
        IconTile("cpu", label="model", color=theme.ATTENTION),
    ).arrange(RIGHT, buff=0.9)


def _glow():
    """Glow on, beside the same shape with it off — the house 'this is live' cue."""
    from manim import RIGHT, VGroup

    lit_core = IconTile("zap", color=theme.TOKEN, size=2.4)
    lit = VGroup(effects.glow(lit_core.tile, theme.TOKEN), lit_core)
    dark = IconTile("zap", color=theme.TOKEN, size=2.4)
    return VGroup(dark, lit).arrange(RIGHT, buff=1.4)


def _station_with_icon():
    station = Station(
        "Tokenizer", subtitle="text → ids", icon="binary", accent=theme.TOKEN
    )
    station.load(TokenStrip("How does ChatGPT work?", per_line=3, show_ids=True))
    return station


def _station():
    station = Station("Tokenizer", subtitle="text → ids", marquee="TOKENIZE")
    station.load(TokenStrip("How does ChatGPT work?", per_line=3, show_ids=True))
    return station


def _station_marquee():
    """The wide-shot state. Guards the marquee's size and placement."""
    station = Station("Sampling", subtitle="vector → token", marquee="SAMPLE")
    station.reveal_marquee()
    return station


def _pipeline_box():
    stations = [
        Station(name, width=4.2, height=3.4)
        for name in ("Tokenizer", "Embedding", "Transformer", "Sampling")
    ]
    for i, station in enumerate(stations):
        station.move_to(np.array([i * 4.8 - 7.2, 0.0, 0.0]))
    # PipelineBox encloses without owning — stations are positioned and added
    # independently by the set — so the case must draw both.
    box = PipelineBox(stations, title="THE MODEL", subtitle="one forward pass")
    return VGroup(box, *stations).scale(0.42)


def _conveyor():
    return Conveyor(
        [[-5, 1.5, 0], [2, 1.5, 0], [2, -1.5, 0], [5, -1.5, 0]], chevrons=4
    )


def _streaming_bubble():
    bubble = StreamingBubble(
        "It turns your words into numbers, then predicts the next one.", max_width=4.0
    )
    bubble.reveal(5)
    return bubble.scale(1.8)


#: name -> factory. Names become a JSON baseline of the same name.
CASES: dict[str, Callable[[], Mobject]] = {
    "chat_window": _chat_window,
    "typing_indicator": lambda: TypingIndicator().scale(3),
    "token_strip": _token_strip,
    "vector_column": _vector_column,
    "embedding_grid": lambda: _embedding_grid().scale(1.6),
    "request_path": lambda: RequestPath().scale(0.9),
    "server_rack": lambda: ServerRack().scale(2),
    "probability_chart": _probability_chart,
    "transformer_stack": lambda: TransformerStack(n_layers=96, shown=4, label="96 layers"),
    "attention_matrix": lambda: AttentionMatrix(["How", "does", "it", "work"]).scale(1.6),
    "station": _station,
    "station_marquee": _station_marquee,
    "pipeline_box": _pipeline_box,
    "conveyor": _conveyor,
    "streaming_bubble": _streaming_bubble,
    "glyph_row": _glyph_row,
    "icon_tile": _icon_tile,
    "glow": _glow,
    "station_with_icon": _station_with_icon,
}
