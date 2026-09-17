"""Probability distributions and sampling.

The "which token comes next" half of an LLM explainer: bar charts over
candidate tokens, temperature effects, and the sampling pick.
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

from manim import DOWN, LEFT, RIGHT, UP, Rectangle, VGroup

from lib import theme, utils


def softmax(logits: Sequence[float], temperature: float = 1.0) -> list[float]:
    """Standard softmax with temperature. ``temperature`` must be > 0."""
    if temperature <= 0:
        raise ValueError("temperature must be > 0")
    scaled = [x / temperature for x in logits]
    peak = max(scaled)
    exps = [math.exp(x - peak) for x in scaled]
    total = sum(exps)
    return [e / total for e in exps]


class ProbabilityBar(VGroup):
    """One labelled horizontal bar: a candidate token and its probability."""

    def __init__(
        self,
        label: str,
        value: float,
        *,
        max_value: float = 1.0,
        bar_length: float = 3.0,
        bar_height: float = 0.32,
        label_width: float = 1.3,
        color=None,
        show_value: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.value = value
        self.accent = color or theme.PROB

        self.label_mob = utils._text(label, theme.SIZE_CAPTION, theme.FG, theme.FONT_MONO)
        utils.fit_text(self.label_mob, label_width)

        self.track = Rectangle(
            width=bar_length,
            height=bar_height,
            fill_color=theme.SURFACE,
            fill_opacity=1.0,
            stroke_width=0,
        )
        filled = bar_length * min(1.0, value / max_value if max_value else 0.0)
        self.bar = Rectangle(
            width=max(filled, 1e-4),
            height=bar_height,
            fill_color=self.accent,
            fill_opacity=1.0,
            stroke_width=0,
        )
        self.track.next_to(self.label_mob, RIGHT, buff=theme.PAD_MD)
        self.bar.align_to(self.track, LEFT).set_y(self.track.get_y())
        self.add(self.label_mob, self.track, self.bar)

        self.value_mob = None
        if show_value:
            self.value_mob = utils._text(
                f"{value:.2f}", theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_MONO
            ).next_to(self.track, RIGHT, buff=theme.PAD_SM)
            self.add(self.value_mob)

    def set_value(self, value: float, *, max_value: float = 1.0) -> "ProbabilityBar":
        """Resize the bar in place (use inside ``.animate`` for a smooth change)."""
        target = self.track.width * min(1.0, value / max_value if max_value else 0.0)
        self.bar.stretch_to_fit_width(max(target, 1e-4))
        self.bar.align_to(self.track, LEFT)
        self.value = value
        if self.value_mob is not None:
            new = utils._text(
                f"{value:.2f}", theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_MONO
            ).move_to(self.value_mob)
            self.remove(self.value_mob)
            self.value_mob = new
            self.add(new)
        return self

    def emphasise(self, color=None) -> "ProbabilityBar":
        self.bar.set_fill(color or theme.TOKEN, opacity=1.0)
        self.label_mob.set_color(color or theme.TOKEN)
        return self

    def deemphasise(self, opacity: float = 0.35) -> "ProbabilityBar":
        self.bar.set_fill(opacity=opacity)
        self.label_mob.set_opacity(opacity)
        return self


class ProbabilityChart(VGroup):
    """A ranked bar chart over candidate next tokens.

    Accepts either probabilities (``{"token": 0.42}``) or raw logits plus a
    temperature, so a scene can show the same distribution sharpen or flatten.
    """

    def __init__(
        self,
        distribution: Mapping[str, float],
        *,
        logits: bool = False,
        temperature: float = 1.0,
        top_k: int | None = None,
        bar_length: float = 3.0,
        gap: float = theme.PAD_SM,
        color=None,
        title: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        items = list(distribution.items())
        if logits:
            probs = softmax([v for _, v in items], temperature)
            items = [(k, p) for (k, _), p in zip(items, probs)]
        items.sort(key=lambda kv: kv[1], reverse=True)
        if top_k is not None:
            items = items[:top_k]
        self.items = items

        top = items[0][1] if items else 1.0
        self.bars = VGroup(
            *[
                ProbabilityBar(k, v, max_value=top, bar_length=bar_length, color=color)
                for k, v in items
            ]
        ).arrange(DOWN, buff=gap, aligned_edge=LEFT)
        self.add(self.bars)

        self.title_mob = None
        if title:
            self.title_mob = utils.label(title).next_to(self.bars, UP, buff=theme.PAD_MD)
            self.title_mob.align_to(self.bars, LEFT)
            self.add(self.title_mob)

    def __len__(self) -> int:
        return len(self.bars)

    def bar_for(self, token: str) -> ProbabilityBar | None:
        for (name, _), bar in zip(self.items, self.bars):
            if name == token:
                return bar
        return None

    def select(self, token: str, *, dim_others: float = 0.3) -> ProbabilityBar | None:
        """Highlight the sampled token and dim the rest."""
        chosen = self.bar_for(token)
        for bar in self.bars:
            if bar is chosen:
                bar.emphasise()
            else:
                bar.deemphasise(dim_others)
        return chosen

    def probabilities(self) -> list[float]:
        return [v for _, v in self.items]


__all__ = ["ProbabilityBar", "ProbabilityChart", "softmax"]
