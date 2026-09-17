"""Vectors and embeddings — the continuous-number layer.

Anything that turns a symbol into an array of floats, or shows arrays being
compared, lives here: embedding columns, matrices, heatmap grids, and 2-D
"semantic space" projections.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Dot,
    Square,
    VGroup,
    interpolate_color,
)

from lib import theme, utils


def stable_vector(seed_text: str, dim: int = 6, *, lo: float = -1.0, hi: float = 1.0):
    """Deterministic pseudo-random vector derived from a string.

    Deterministic so that the same token always shows the same numbers across
    scenes, sessions and snapshot tests.
    """
    acc = 2166136261
    for ch in seed_text:
        acc = ((acc ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    values = []
    for i in range(dim):
        acc = (acc * 1103515245 + 12345) & 0x7FFFFFFF
        values.append(lo + (hi - lo) * (acc / 0x7FFFFFFF))
    return np.array(values)


class VectorColumn(VGroup):
    """A column of numbers in a bracketed box — one embedding.

    ``truncate_at`` inserts an ellipsis row so a 1536-dim vector reads as huge
    without drawing 1536 numbers.
    """

    def __init__(
        self,
        values: Sequence[float],
        *,
        label: str | None = None,
        color=None,
        decimals: int = 2,
        truncate_at: int | None = 6,
        font_size: float = theme.SIZE_CAPTION,
        width: float = 1.15,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.values = list(values)
        self.accent = color or theme.EMBED

        shown: list[str] = []
        if truncate_at is not None and len(self.values) > truncate_at:
            head = self.values[: truncate_at - 2]
            shown = [f"{v:+.{decimals}f}" for v in head] + ["⋮", f"{self.values[-1]:+.{decimals}f}"]
        else:
            shown = [f"{v:+.{decimals}f}" for v in self.values]

        self.rows = VGroup(
            *[utils._text(s, font_size, theme.FG, theme.FONT_MONO) for s in shown]
        ).arrange(DOWN, buff=theme.PAD_XS)

        self.box = utils.panel(
            width=max(width, self.rows.width + 2 * theme.PAD_SM),
            height=self.rows.height + 2 * theme.PAD_SM,
            fill=theme.SURFACE,
            stroke=self.accent,
            stroke_width=theme.STROKE_NORMAL,
        )
        self.rows.move_to(self.box.get_center())
        self.add(self.box, self.rows)

        self.label_mob = None
        if label:
            self.label_mob = utils._text(
                label, theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_MONO
            ).next_to(self.box, UP, buff=theme.PAD_XS)
            self.add(self.label_mob)

    @property
    def dimension(self) -> int:
        """Number of values in the underlying vector (``dim`` is taken by Mobject)."""
        return len(self.values)


class EmbeddingGrid(VGroup):
    """A matrix of coloured cells — a heatmap of ``rows x cols`` activations.

    Used for "one row per token, one column per dimension" views and for
    attention matrices (see :mod:`lib.components.transformer`).
    """

    def __init__(
        self,
        data,
        *,
        cell: float = 0.26,
        gap: float = 0.03,
        low_color=None,
        high_color=None,
        row_labels: Sequence[str] | None = None,
        col_labels: Sequence[str] | None = None,
        rotate_col_labels: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        matrix = np.array(data, dtype=float)
        if matrix.ndim != 2:
            raise ValueError("EmbeddingGrid expects a 2-D array")
        self.matrix = matrix
        low_color = low_color or theme.BG_ELEVATED
        high_color = high_color or (theme.EMBED)

        lo, hi = float(matrix.min()), float(matrix.max())
        span = (hi - lo) or 1.0

        self.cells = VGroup()
        for r in range(matrix.shape[0]):
            row = VGroup()
            for c in range(matrix.shape[1]):
                t = (matrix[r, c] - lo) / span
                sq = Square(
                    side_length=cell,
                    fill_color=interpolate_color(low_color, high_color, t),
                    fill_opacity=1.0,
                    stroke_width=0,
                )
                row.add(sq)
            row.arrange(RIGHT, buff=gap)
            self.cells.add(row)
        self.cells.arrange(DOWN, buff=gap)
        self.add(self.cells)

        if row_labels:
            self.row_label_mobs = VGroup(
                *[
                    utils._text(t, theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_MONO).next_to(
                        self.cells[i], LEFT, buff=theme.PAD_SM
                    )
                    for i, t in enumerate(row_labels[: matrix.shape[0]])
                ]
            )
            self.add(self.row_label_mobs)
        if col_labels:
            # Narrow cells cannot fit a horizontal label, so rotate rather than
            # let neighbouring labels collide.
            mobs = []
            for i, t in enumerate(col_labels[: matrix.shape[1]]):
                lab = utils._text(t, theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_MONO)
                if rotate_col_labels:
                    lab.rotate(np.pi / 2)
                else:
                    utils.fit_text(lab, cell)
                lab.next_to(self.cells[0][i], UP, buff=theme.PAD_SM)
                mobs.append(lab)
            self.col_label_mobs = VGroup(*mobs)
            self.add(self.col_label_mobs)

    def cell_at(self, row: int, col: int) -> Square:
        return self.cells[row][col]


class VectorArrow(VGroup):
    """A labelled 2-D arrow from the origin — for "semantic space" diagrams."""

    def __init__(
        self,
        x: float,
        y: float,
        *,
        label: str | None = None,
        color=None,
        origin=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        color = color or theme.EMBED
        start = np.array([0.0, 0.0, 0.0]) if origin is None else np.array(origin, dtype=float)
        end = start + np.array([x, y, 0.0])
        self.arrow = Arrow(
            start=start,
            end=end,
            buff=0,
            color=color,
            stroke_width=theme.STROKE_NORMAL,
            max_tip_length_to_length_ratio=0.18,
        )
        self.add(self.arrow)
        self.label_mob = None
        if label:
            self.label_mob = utils._text(
                label, theme.SIZE_MICRO, color, theme.FONT_BODY
            ).next_to(self.arrow.get_end(), UP if y >= 0 else DOWN, buff=theme.PAD_XS)
            self.add(self.label_mob)

    @property
    def angle(self) -> float:
        vec = self.arrow.get_end() - self.arrow.get_start()
        return math.atan2(vec[1], vec[0])


class SemanticSpace(VGroup):
    """A 2-D scatter of labelled points — "similar meanings sit close together"."""

    def __init__(
        self,
        points: dict[str, tuple[float, float]],
        *,
        radius: float = 0.07,
        color=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        color = color or theme.EMBED
        self.dots = VGroup()
        self.labels = VGroup()
        for name, (x, y) in points.items():
            dot = Dot(point=[x, y, 0], radius=radius, color=color)
            lab = utils._text(name, theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_BODY)
            lab.next_to(dot, UP, buff=theme.PAD_XS)
            self.dots.add(dot)
            self.labels.add(lab)
        self.add(self.dots, self.labels)


__all__ = [
    "VectorColumn",
    "EmbeddingGrid",
    "VectorArrow",
    "SemanticSpace",
    "stable_vector",
]
