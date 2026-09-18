"""Contracts for the glow/trail effects and the icon components."""

import pytest
from manim import Dot, RoundedRectangle, Square

from lib import effects, theme
from lib.components.glyph import Glyph, IconTile, available_icons, icon_path


# ----------------------------------------------------------------- effects
def _ring():
    return RoundedRectangle(
        width=2.0, height=2.0, corner_radius=0.3,
        stroke_color=theme.TOKEN, stroke_width=2,
    ).set_fill(opacity=0)


def test_glow_produces_the_requested_number_of_layers():
    assert len(effects.glow(_ring(), theme.TOKEN, layers=9)) == 9


def test_glow_rejects_zero_layers():
    with pytest.raises(ValueError):
        effects.glow(_ring(), theme.TOKEN, layers=0)


def test_glow_layers_widen_and_fade_outward():
    """Widest layer must be the faintest, or it reads as a fog, not a glow."""
    halo = effects.glow(_ring(), theme.TOKEN, layers=8)
    widths = [layer.get_stroke_width() for layer in halo]
    opacities = [layer.get_stroke_opacity() for layer in halo]
    assert widths[0] > widths[-1]
    assert opacities[0] < opacities[-1]


def test_glow_extends_beyond_its_source():
    """Measured on stroke width, not bounding box.

    Manim's `.width` is path geometry and ignores stroke, so the halo copies
    share the source's bounding box exactly — the light spills out through
    stroke width alone.
    """
    ring = _ring()
    halo = effects.glow(ring, theme.TOKEN)
    assert max(layer.get_stroke_width() for layer in halo) > ring.get_stroke_width()


def test_glow_does_not_mutate_its_source():
    ring = _ring()
    before = (ring.get_stroke_width(), ring.get_stroke_opacity())
    effects.glow(ring, theme.TOKEN)
    assert (ring.get_stroke_width(), ring.get_stroke_opacity()) == before


def test_glowing_starts_off_and_toggles():
    node = effects.Glowing(_ring(), theme.TOKEN)
    assert not node.is_on
    assert node.halo.get_stroke_opacity() == pytest.approx(0.0)
    node.on()
    assert node.is_on
    node.off()
    assert not node.is_on


def test_glowing_can_start_on():
    assert effects.Glowing(_ring(), theme.TOKEN, start_on=True).is_on


def test_glowing_renders_halo_behind_core():
    node = effects.Glowing(_ring(), theme.TOKEN)
    assert node.submobjects.index(node.halo) < node.submobjects.index(node.core)


def test_glowing_dim_leaves_residual_light():
    node = effects.Glowing(_ring(), theme.TOKEN)
    node.dim_glow(0.4)
    assert node.is_on
    assert 0 < node.halo.get_stroke_opacity() < 1


def test_comet_follows_its_dot():
    dot = Dot(color=theme.TOKEN)
    trail = effects.comet(dot)
    assert trail.stroke_color.to_hex() == theme.TOKEN.to_hex()


# ------------------------------------------------------------------ glyph
def test_icon_set_is_vendored_and_non_empty():
    icons = available_icons()
    assert len(icons) >= 20
    assert "server" in icons and "cpu" in icons


def test_missing_icon_names_the_alternatives():
    with pytest.raises(FileNotFoundError, match="Available"):
        icon_path("definitely-not-an-icon")


def test_glyph_is_stroked_not_filled():
    """Lucide icons are outlines; filling them makes them look like blobs."""
    glyph = Glyph("cpu", color=theme.EMBED, height=1.0)
    strokes = [p for p in glyph.parts if not getattr(p, "_is_indicator_dot", False)]
    assert strokes, "icon must have stroked paths"
    assert all(p.get_fill_opacity() == pytest.approx(0.0) for p in strokes)
    assert all(p.get_stroke_width() > 0 for p in strokes)


def test_glyph_restores_degenerate_indicator_dots():
    """Lucide draws status lights as zero-length lines, which Manim renders as
    nothing. The server icon must keep both of its lights."""
    glyph = Glyph("server", color=theme.NETWORK)
    dots = [p for p in glyph.parts if getattr(p, "_is_indicator_dot", False)]
    assert len(dots) == 2
    assert all(d.get_fill_opacity() > 0 for d in dots)
    assert all(d.width > 0 for d in dots)


def test_glyph_honours_requested_height():
    assert Glyph("zap", height=1.6).height == pytest.approx(1.6, rel=1e-6)


def test_glyph_recolor_covers_dots_and_strokes():
    glyph = Glyph("server", color=theme.NETWORK)
    glyph.recolor(theme.PROB)
    for part in glyph.parts:
        if getattr(part, "_is_indicator_dot", False):
            assert part.get_fill_color().to_hex() == theme.PROB.to_hex()
        else:
            assert part.get_stroke_color().to_hex() == theme.PROB.to_hex()


def test_icon_tile_centres_its_glyph_and_exposes_anchors():
    tile = IconTile("database", label="storage", color=theme.EMBED, size=2.4)
    assert tile.glyph.get_center()[0] == pytest.approx(tile.tile.get_center()[0], abs=1e-6)
    assert tile.glyph.height < tile.tile.height
    assert tile.entry[0] < tile.exit[0]
    assert tile.label_mob is not None


def test_icon_tile_label_is_optional():
    assert IconTile("cloud").label_mob is None


def test_icon_tile_recolor_updates_tile_and_glyph():
    tile = IconTile("cloud", color=theme.NETWORK)
    tile.recolor(theme.TOKEN)
    assert tile.tile.get_stroke_color().to_hex() == theme.TOKEN.to_hex()
    assert tile.accent.to_hex() == theme.TOKEN.to_hex()


def test_station_accepts_an_icon():
    from lib.components.factory import Station

    station = Station("Tokenizer", subtitle="text to ids", icon="binary")
    assert station.icon is not None
    # Content must still land below the whole header, icon included.
    station.load(Square(side_length=0.5))
    assert station.content[0].get_top()[1] < station.header.get_bottom()[1]


def test_station_without_an_icon_still_works():
    from lib.components.factory import Station

    assert Station("Plain").icon is None
