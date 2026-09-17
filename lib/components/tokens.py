"""Tokens: the discrete-symbol layer of every LLM explainer.

Covers the chip that represents one token, strips/grids of them, the token-id
badge, and a deliberately simple demo tokenizer so scenes can show a realistic
split without depending on a real BPE vocabulary at render time.
"""

from __future__ import annotations

import re
from typing import Iterable, Sequence

from manim import DOWN, LEFT, RIGHT, UP, Mobject, VGroup

from lib import theme, utils

#: Characters shown in place of whitespace so a leading-space token is visible.
SPACE_GLYPH = "␣"


def simple_tokenize(text: str) -> list[str]:
    """Split ``text`` into BPE-ish tokens: leading space kept with the word.

    This is a *pedagogical* tokenizer, not tiktoken. It reproduces the two
    things a viewer needs to see — that whitespace belongs to the token, and
    that long words break into pieces — without a vocabulary file. If a scene
    needs true GPT tokens, pass them in explicitly rather than relying on this.
    """
    raw = re.findall(r"\s*\w+|\s*[^\w\s]", text)
    out: list[str] = []
    for piece in raw:
        stripped = piece.strip()
        # Break long words the way a subword tokenizer would.
        if len(stripped) > 7 and stripped.isalpha():
            lead = piece[: len(piece) - len(stripped)]
            head, tail = stripped[:4], stripped[4:]
            out.append(lead + head)
            while tail:
                out.append(tail[:4])
                tail = tail[4:]
        else:
            out.append(piece)
    return out


def display_token(token: str) -> str:
    """Render whitespace visibly so token boundaries read on screen."""
    return token.replace(" ", SPACE_GLYPH).replace("\n", "⏎")


class TokenChip(VGroup):
    """One token, drawn as a rounded chip.

    ``token_id`` is optional; when given it is shown as a small badge beneath.
    """

    def __init__(
        self,
        token: str,
        *,
        token_id: int | None = None,
        color=None,
        font_size: float = theme.SIZE_LABEL,
        min_width: float = 0.5,
        show_id: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.token = token
        self.token_id = token_id
        self.accent = color or theme.TOKEN

        self.text_mob = utils._text(
            display_token(token), font_size, theme.FG, theme.FONT_MONO
        )
        self.box = utils.panel(
            width=max(min_width, self.text_mob.width + 2 * theme.PAD_SM),
            height=self.text_mob.height + 2 * theme.PAD_SM,
            fill=theme.SURFACE,
            stroke=self.accent,
            stroke_width=theme.STROKE_NORMAL,
        )
        self.text_mob.move_to(self.box.get_center())
        self.add(self.box, self.text_mob)

        self.id_mob = None
        if show_id and token_id is not None:
            self.id_mob = utils._text(
                str(token_id), theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_MONO
            )
            self.id_mob.next_to(self.box, DOWN, buff=theme.PAD_XS)
            self.add(self.id_mob)

    def highlight(self, color=None, *, width: float = theme.STROKE_THICK) -> "TokenChip":
        """Thicken and recolour the chip border — the standard "this one" cue."""
        self.box.set_stroke(color or theme.EMBED, width=width)
        return self

    def reset_highlight(self) -> "TokenChip":
        self.box.set_stroke(self.accent, width=theme.STROKE_NORMAL)
        return self


class TokenStrip(VGroup):
    """A row (or wrapped rows) of ``TokenChip``s built from text or a token list.

    Parameters
    ----------
    source:
        Either a string (tokenized with :func:`simple_tokenize`) or an explicit
        sequence of token strings.
    token_ids:
        Optional ids, aligned with the tokens. Auto-generated deterministically
        when ``show_ids`` is set and no ids are supplied.
    per_line:
        Wrap after this many chips. ``None`` keeps everything on one row.
    """

    def __init__(
        self,
        source: str | Sequence[str],
        *,
        token_ids: Sequence[int] | None = None,
        per_line: int | None = None,
        show_ids: bool = False,
        gap: float = theme.PAD_XS,
        row_gap: float = theme.PAD_MD,
        color=None,
        font_size: float = theme.SIZE_LABEL,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.tokens = (
            simple_tokenize(source) if isinstance(source, str) else list(source)
        )
        if token_ids is None and show_ids:
            token_ids = [fake_token_id(t) for t in self.tokens]
        self.token_ids = list(token_ids) if token_ids is not None else None

        self.chips = VGroup(
            *[
                TokenChip(
                    tok,
                    token_id=None if self.token_ids is None else self.token_ids[i],
                    show_id=show_ids,
                    color=color,
                    font_size=font_size,
                )
                for i, tok in enumerate(self.tokens)
            ]
        )

        rows = (
            [list(self.chips)]
            if per_line is None
            else utils.wrap_words(list(self.chips), per_line)
        )
        self.rows = VGroup(*[VGroup(*row).arrange(RIGHT, buff=gap) for row in rows])
        self.rows.arrange(DOWN, buff=row_gap, aligned_edge=LEFT)
        self.add(self.rows)

    def __len__(self) -> int:
        return len(self.chips)

    def __getitem__(self, index):  # type: ignore[override]
        return self.chips[index]

    def chip_for(self, token: str) -> TokenChip | None:
        for chip in self.chips:
            if chip.token == token:
                return chip
        return None

    def highlight_all(self, color=None) -> "TokenStrip":
        for chip in self.chips:
            chip.highlight(color)
        return self

    def reset_all(self) -> "TokenStrip":
        for chip in self.chips:
            chip.reset_highlight()
        return self


def fake_token_id(token: str) -> int:
    """Stable, plausible-looking token id for a token string.

    Deterministic across sessions and machines (no ``hash()`` randomisation) so
    snapshot tests and re-renders stay identical.
    """
    acc = 0
    for ch in token:
        acc = (acc * 131 + ord(ch)) % 50257  # GPT-2 vocab size, for flavour
    return acc


__all__ = [
    "TokenChip",
    "TokenStrip",
    "simple_tokenize",
    "display_token",
    "fake_token_id",
    "SPACE_GLYPH",
]
