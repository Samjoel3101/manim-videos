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
from manim import Mobject

from lib.components.chat_ui import ChatWindow, TypingIndicator
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


#: name -> factory. Names become ``tests/baselines/<name>.json``.
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
}
