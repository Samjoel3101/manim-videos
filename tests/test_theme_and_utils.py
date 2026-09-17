"""Foundation checks: the theme contract every component depends on."""

import pytest
from manim import Text

from lib import theme, utils


def test_palette_is_hex_and_distinct():
    named = [theme.BG, theme.FG, theme.USER, theme.ASSISTANT, theme.TOKEN,
             theme.EMBED, theme.ATTENTION, theme.PROB, theme.NETWORK]
    hexes = [c.to_hex() for c in named]
    assert len(set(hexes)) == len(hexes), "two semantic colours collide"


def test_series_color_wraps():
    assert theme.series_color(0) == theme.SERIES[0]
    assert theme.series_color(len(theme.SERIES)) == theme.SERIES[0]


def test_spacing_is_a_multiple_of_the_unit():
    for pad in (theme.PAD_XS, theme.PAD_SM, theme.PAD_MD, theme.PAD_LG, theme.PAD_XL):
        assert abs((pad / theme.UNIT) % 0.5) < 1e-9


def test_type_scale_is_descending():
    sizes = [theme.SIZE_TITLE, theme.SIZE_HEADING, theme.SIZE_BODY,
             theme.SIZE_LABEL, theme.SIZE_CAPTION, theme.SIZE_MICRO]
    assert sizes == sorted(sizes, reverse=True)


def test_text_helpers_apply_theme_colours():
    # Manim keeps Text colour on the per-glyph submobjects, not the group.
    assert utils.body("x")[0].fill_color.to_hex() == theme.FG.to_hex()
    assert utils.label("x")[0].fill_color.to_hex() == theme.FG_MUTED.to_hex()


def test_fit_text_shrinks_but_never_grows():
    wide = Text("a very long line of text indeed", font_size=40)
    before = wide.width
    utils.fit_text(wide, before / 2)
    assert wide.width <= before / 2 + 1e-6

    small = Text("hi", font_size=10)
    w = small.width
    utils.fit_text(small, 10.0)
    assert small.width == pytest.approx(w)


def test_wrap_words_chunks_and_rejects_zero():
    assert utils.wrap_words(list("abcde"), 2) == [["a", "b"], ["c", "d"], ["e"]]
    with pytest.raises(ValueError):
        utils.wrap_words(["a"], 0)


def test_is_in_frame_detects_overflow():
    small = Text("ok", font_size=20)
    assert utils.is_in_frame(small)
    huge = Text("ok", font_size=20).scale(40)
    assert not utils.is_in_frame(huge)
