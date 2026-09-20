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
from lib.components.checks import CheckList
from lib.components.factory import Conveyor, PipelineBox, Station
from lib.components.glyph import Glyph, IconTile
from lib.components.network import RequestPath, ServerRack
from lib.components.probability import ProbabilityChart
from lib.components.stacked import SegmentedBar
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


def _station_wide_bar():
    """The wide short bay a vertical column uses: header left, content right."""
    station = Station(
        "Tokenizer",
        subtitle="text → ids",
        icon="binary",
        accent=theme.TOKEN,
        width=7.8,
        height=2.4,
        header_side="left",
        shot_width=11.0,
    )
    station.load(TokenStrip("How does ChatGPT work?"))
    return station.scale(1.5)


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


def _check_list():
    """A half-ticked list: the state the viewer actually sees mid-beat.

    Guards the three reserved columns and, just as importantly, that the tick
    is drawn as an outline mark on a filled disc rather than as a blob — the
    fill-vs-stroke failure would show up here as a solid marker.
    """
    checks = CheckList(
        ["WAF", ("bot score", "0.02"), ("rate limit", "12 / 60")],
        width=3.4,
        frame_width=13.6,
    )
    checks[0].mark_pass()
    checks[1].mark_pass()
    return checks.scale(2.4)


def _segmented_bar_legend():
    """The orchestrator's prompt bar. The 7-token sliver must be visible."""
    return SegmentedBar(
        {
            "system prompt": 2400,
            "tool definitions": 1150,
            "memory + prefs": 380,
            "your message": 7,
        },
        length=5.0,
        thickness=0.6,
        labels="legend",
        min_segment=0.035,
        colors=[theme.NETWORK, theme.ATTENTION, theme.EMBED, theme.USER],
        frame_width=13.6,
        # Bar plus legend is ~9.8 units wide; 1.5x overflowed a 14-unit frame
        # and cut the values off the right-hand side.
    ).scale(1.15)


def _segmented_bar_legend_below():
    """The orchestrator's bar as the film now draws it: legend UNDER the bar.

    Guards the layout that makes the four names readable. Beside a bar short
    enough to leave room for it, a legend gives "tool definitions" ~0.6 units
    against the 2.10 it needs, and the old component shrank the NAME column
    alone — names at ~0.3x the height of their own numbers. Under the bar the
    legend has the bar's full width, so both columns stay at one size and the
    numbers right-align with the bar's end.
    """
    return SegmentedBar(
        {
            "system prompt": 2400,
            "tool definitions": 1150,
            "memory + prefs": 380,
            "your message": 7,
        },
        length=6.0,
        thickness=0.5,
        labels="legend",
        legend_side="below",
        strict_legend=True,
        min_segment=0.035,
        colors=[theme.NETWORK, theme.ATTENTION, theme.EMBED, theme.TOKEN],
        frame_width=13.6,
    ).scale(1.15)


def _segmented_bar_inline():
    """The KV-cache bar, emphasised. Guards the inline-label width rule: the
    narrow "new tail" segment gets no label of its own, by design."""
    bar = SegmentedBar(
        {"cached prefix": 3900, "new tail": 37},
        length=6.0,
        thickness=0.6,
        labels="inline",
        min_segment=0.05,
        # Explicit: below INLINE_MIN_FRACTION, so "new tail" is drawn without a
        # label. That is precisely what this case guards, and SegmentedBar now
        # makes a caller say so rather than discovering it in a render.
        allow_unlabelled_segments=True,
        colors=[theme.FG_FAINT, theme.TOKEN],
        frame_width=13.6,
    )
    bar.emphasise("new tail")
    return bar.scale(1.6)


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
    "station_wide_bar": _station_wide_bar,
    "check_list": _check_list,
    "segmented_bar_legend": _segmented_bar_legend,
    "segmented_bar_legend_below": _segmented_bar_legend_below,
    "segmented_bar_inline": _segmented_bar_inline,
}
