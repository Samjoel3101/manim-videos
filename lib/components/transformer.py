"""Transformer internals: layer stacks, attention, and the residual stream.

Everything here is schematic, not architecturally exhaustive — the goal is a
viewer's mental model, so a "layer" is a labelled block and "attention" is a
set of weighted lines between token positions.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, Arrow, Line, VGroup

from lib import theme, utils
from lib.components.vectors import EmbeddingGrid


class LayerBlock(VGroup):
    """One labelled block in a stack — a transformer layer, an MLP, a norm."""

    def __init__(
        self,
        title: str,
        *,
        subtitle: str | None = None,
        width: float = 3.4,
        height: float = 0.7,
        color=None,
        fill=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.accent = color or theme.ATTENTION
        self.box = utils.panel(
            width=width,
            height=height,
            fill=fill or theme.BG_ELEVATED,
            stroke=self.accent,
            stroke_width=theme.STROKE_NORMAL,
        )
        self.title_mob = utils._text(title, theme.SIZE_CAPTION, theme.FG, theme.FONT_BODY)
        utils.fit_text(self.title_mob, width - 2 * theme.PAD_MD)
        content = VGroup(self.title_mob)
        if subtitle:
            self.subtitle_mob = utils._text(
                subtitle, theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_MONO
            )
            content.add(self.subtitle_mob)
            content.arrange(DOWN, buff=theme.PAD_XS)
        content.move_to(self.box.get_center())
        self.add(self.box, content)

    def activate(self, color=None) -> "LayerBlock":
        """Light this block up — the "currently executing" cue in a stack pass."""
        self.box.set_stroke(color or theme.TOKEN, width=theme.STROKE_THICK)
        self.box.set_fill(theme.SURFACE, opacity=1.0)
        return self

    def deactivate(self) -> "LayerBlock":
        self.box.set_stroke(self.accent, width=theme.STROKE_NORMAL)
        self.box.set_fill(theme.BG_ELEVATED, opacity=1.0)
        return self


class TransformerStack(VGroup):
    """A stack of layers with an optional ellipsis for the omitted middle.

    ``n_layers`` is the *real* depth the label reports; ``shown`` is how many
    blocks are actually drawn.
    """

    def __init__(
        self,
        *,
        n_layers: int = 96,
        shown: int = 4,
        width: float = 3.4,
        block_height: float = 0.62,
        gap: float = theme.PAD_SM,
        label: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if shown < 2:
            raise ValueError("shown must be >= 2 to render a stack with an ellipsis")
        self.n_layers = n_layers
        self.blocks = VGroup()
        elide = n_layers > shown

        for i in range(shown):
            index = i + 1 if i < shown - 1 else n_layers
            self.blocks.add(
                LayerBlock(
                    f"Layer {index}",
                    subtitle="attention + MLP",
                    width=width,
                    height=block_height,
                )
            )

        self.ellipsis = None
        items: list = list(self.blocks)
        if elide:
            self.ellipsis = utils._text("⋮", theme.SIZE_HEADING, theme.FG_FAINT, theme.FONT_BODY)
            items.insert(len(items) - 1, self.ellipsis)

        self.column = VGroup(*items).arrange(UP, buff=gap)
        self.add(self.column)

        self.label_mob = None
        if label:
            self.label_mob = utils.label(label).next_to(self.column, DOWN, buff=theme.PAD_MD)
            self.add(self.label_mob)

    def __len__(self) -> int:
        return len(self.blocks)

    def __getitem__(self, index):  # type: ignore[override]
        return self.blocks[index]

    def sweep(self, scene, *, run_time: float = theme.T_FAST) -> None:
        """Animate activation travelling bottom-to-top through the stack."""
        for block in self.blocks:
            scene.play(block.animate.activate(), run_time=run_time * 0.5)
            scene.play(block.animate.deactivate(), run_time=run_time * 0.5)


class AttentionLines(VGroup):
    """Weighted lines from one query position to every key position.

    ``weights`` should sum to ~1; line opacity and width encode the weight, so
    a viewer reads "this token is looking mostly at that one".
    """

    def __init__(
        self,
        query_mob,
        key_mobs: Sequence,
        weights: Sequence[float],
        *,
        color=None,
        max_width: float = 5.0,
        min_opacity: float = 0.08,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if len(key_mobs) != len(weights):
            raise ValueError("key_mobs and weights must be the same length")
        color = color or theme.ATTENTION
        self.weights = list(weights)
        peak = max(weights) if weights else 1.0

        self.lines = VGroup()
        for key, w in zip(key_mobs, weights):
            rel = (w / peak) if peak else 0.0
            self.lines.add(
                Line(
                    query_mob.get_top(),
                    key.get_bottom(),
                    stroke_color=color,
                    stroke_width=max(0.4, max_width * rel),
                    stroke_opacity=max(min_opacity, rel),
                )
            )
        self.add(self.lines)

    def strongest(self) -> int:
        return int(np.argmax(self.weights)) if self.weights else -1


class AttentionMatrix(EmbeddingGrid):
    """A token x token attention heatmap — a causal mask is applied by default."""

    def __init__(
        self,
        tokens: Sequence[str],
        weights=None,
        *,
        causal: bool = True,
        cell: float = 0.36,
        **kwargs,
    ) -> None:
        n = len(tokens)
        if weights is None:
            # Deterministic filler so the visual is stable across renders.
            base = np.array([[1.0 / (1 + abs(i - j)) for j in range(n)] for i in range(n)])
        else:
            base = np.array(weights, dtype=float)
        if causal:
            base = np.tril(base)
        rows = base.sum(axis=1, keepdims=True)
        rows[rows == 0] = 1.0
        normalised = base / rows
        super().__init__(
            normalised,
            cell=cell,
            row_labels=list(tokens),
            col_labels=list(tokens),
            rotate_col_labels=True,
            high_color=theme.ATTENTION,
            **kwargs,
        )
        self.tokens = list(tokens)


class ResidualStream(VGroup):
    """The vertical arrow a representation travels along through the stack."""

    def __init__(self, height: float = 3.0, *, label: str | None = "residual stream", **kwargs):
        super().__init__(**kwargs)
        self.arrow = Arrow(
            start=DOWN * height / 2,
            end=UP * height / 2,
            buff=0,
            color=theme.EMBED,
            stroke_width=theme.STROKE_NORMAL,
            max_tip_length_to_length_ratio=0.06,
        )
        self.add(self.arrow)
        self.label_mob = None
        if label:
            self.label_mob = utils._text(
                label, theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_BODY
            ).next_to(self.arrow, RIGHT, buff=theme.PAD_SM)
            self.add(self.label_mob)


__all__ = [
    "LayerBlock",
    "TransformerStack",
    "AttentionLines",
    "AttentionMatrix",
    "ResidualStream",
]
