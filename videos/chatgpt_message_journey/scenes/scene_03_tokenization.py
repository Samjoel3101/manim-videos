"""Scene 3 — Tokenization.

"Your sentence is chopped up." The model never sees characters; it sees a list
of integers drawn from a fixed vocabulary. Three things have to land: chunks are
not words, a leading space belongs to the token after it, and long words split.

Visuals come from lib/components/tokens.py. The callout bracket below is local
to this scene — it is a one-off, so per the promotion rule it stays here until a
second scene needs it.
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Brace,
    FadeIn,
    FadeOut,
    Scene,
    Write,
)

from lib import theme, utils
from lib.components.tokens import SPACE_GLYPH, TokenStrip, fake_token_id, simple_tokenize

SENTENCE = "How does tokenization work?"


class Tokenization(Scene):
    def construct(self) -> None:
        theme.apply(self)

        title = utils.heading("Tokenization")
        title.to_edge(UP, buff=theme.PAD_XL)
        self.play(Write(title), run_time=theme.T_NORMAL)

        # 1. The sentence as a human reads it.
        sentence = utils.body(SENTENCE)
        self.play(FadeIn(sentence), run_time=theme.T_NORMAL)
        self.wait(theme.T_SLOW)

        # 2. It separates into chips. Same words, now discrete objects.
        # One row: the brace callouts below need the split word's pieces to sit
        # next to each other, and 7 chips fit the frame comfortably.
        strip = TokenStrip(SENTENCE, gap=theme.PAD_SM)
        strip.move_to([0, 0, 0])
        self.play(FadeOut(sentence), run_time=theme.T_FAST)
        self.play(
            *[FadeIn(chip, shift=UP * theme.PAD_XS) for chip in strip.chips],
            lag_ratio=0.12,
            run_time=theme.T_SLOW,
        )
        self.wait(theme.T_BEAT)

        count = utils.label(f"{len(strip)} tokens, not {len(SENTENCE.split())} words")
        count.next_to(strip, DOWN, buff=theme.PAD_LG)
        self.play(FadeIn(count), run_time=theme.T_FAST)
        self.wait(theme.T_SLOW)
        self.play(FadeOut(count), run_time=theme.T_FAST)

        # 3. Call out the leading-space convention on the first token that has one.
        spaced = next(
            (chip for chip in strip.chips if chip.token.startswith(" ")), strip.chips[1]
        )
        self._callout(
            spaced,
            f"the {SPACE_GLYPH} is part of the token —\n" '"does" and " does" are different',
        )

        # 4. Call out a word that the tokenizer had to split.
        fragments = _split_pieces(SENTENCE)
        pieces = [chip for chip in strip.chips if chip.token.strip() in fragments]
        if len(pieces) >= 2:
            self._callout_group(pieces, "long words break into\npieces the model knows")

        # 5. Reveal the integers. This is the point of the scene: the model only
        #    ever sees this list.
        ids = []
        for chip in strip.chips:
            id_mob = utils._text(
                str(fake_token_id(chip.token)),
                theme.SIZE_MICRO,
                theme.FG_MUTED,
                theme.FONT_MONO,
            )
            id_mob.next_to(chip, DOWN, buff=theme.PAD_XS)
            ids.append(id_mob)

        self.play(
            *[chip.animate.highlight(theme.EMBED) for chip in strip.chips],
            run_time=theme.T_FAST,
        )
        self.play(
            *[FadeIn(m, shift=DOWN * theme.PAD_XS) for m in ids],
            lag_ratio=0.1,
            run_time=theme.T_SLOW,
        )
        self.wait(theme.T_BEAT)

        closing = utils.label("The model only ever sees this list of integers.")
        utils.fit_text(closing, 10.0)
        closing.to_edge(DOWN, buff=theme.PAD_XL)
        self.play(FadeIn(closing, shift=UP * theme.PAD_SM), run_time=theme.T_NORMAL)
        self.wait(theme.T_SLOW * 2)

        self.play(
            FadeOut(closing),
            FadeOut(title),
            *[FadeOut(m) for m in ids],
            FadeOut(strip),
            run_time=theme.T_NORMAL,
        )

    # -------------------------------------------------------------- helpers
    def _callout(self, chip, text: str) -> None:
        """Brace one chip and hold an explanation beside it.

        Local to this scene by design — see the module docstring.
        """
        brace = Brace(chip, direction=UP, color=theme.FG_FAINT)
        note = utils._text(text, theme.SIZE_CAPTION, theme.TOKEN, theme.FONT_BODY)
        note.next_to(brace, UP, buff=theme.PAD_SM)
        utils.fit_text(note, 6.0)

        self.play(
            chip.animate.highlight(theme.TOKEN),
            FadeIn(brace),
            FadeIn(note),
            run_time=theme.T_NORMAL,
        )
        self.wait(theme.T_SLOW * 1.5)
        self.play(
            chip.animate.reset_highlight(),
            FadeOut(brace),
            FadeOut(note),
            run_time=theme.T_FAST,
        )

    def _callout_group(self, chips, text: str) -> None:
        from manim import VGroup

        group = VGroup(*chips)
        brace = Brace(group, direction=DOWN, color=theme.FG_FAINT)
        note = utils._text(text, theme.SIZE_CAPTION, theme.TOKEN, theme.FONT_BODY)
        note.next_to(brace, DOWN, buff=theme.PAD_SM)
        utils.fit_text(note, 6.0)

        self.play(
            *[c.animate.highlight(theme.TOKEN) for c in chips],
            FadeIn(brace),
            FadeIn(note),
            run_time=theme.T_NORMAL,
        )
        self.wait(theme.T_SLOW * 1.5)
        self.play(
            *[c.animate.reset_highlight() for c in chips],
            FadeOut(brace),
            FadeOut(note),
            run_time=theme.T_FAST,
        )


def _split_pieces(sentence: str) -> set[str]:
    """Token strings that came from splitting a single long word."""
    tokens = simple_tokenize(sentence)
    words = {w.strip(" ?.,!") for w in sentence.split()}
    return {
        t.strip()
        for t in tokens
        if t.strip() and t.strip().isalnum() and t.strip() not in words
    }
