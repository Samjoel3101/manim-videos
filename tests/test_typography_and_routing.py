"""Contracts for the type system and the path-geometry helpers.

Both modules exist because of bugs that shipped: type that was sized in absolute
points and so became illegible when the camera pulled back, and a travel path
built from node centres that flew through solid boxes.
"""

import numpy as np
import pytest
from manim import Square, VMobject

from lib import routing, theme, typography as typo


# ------------------------------------------------------------- typography
def test_cap_height_calibration_still_holds():
    """Pins the measured constant. A Manim upgrade that changes text metrics
    silently rescales every label in the back catalogue, so fail loudly here."""
    for size in (14, 28, 48, 72):
        measured = typo.text("body", "H", frame_width=12.0, font_size=size).height
        assert measured / size == pytest.approx(typo.CAP_HEIGHT_PER_POINT, rel=0.02)


@pytest.mark.parametrize("role", sorted(typo.ROLES))
def test_role_occupies_the_same_frame_share_at_any_shot(role):
    """The whole point: a role looks the same size regardless of camera width."""
    shares = [
        typo.text(role, "Hxy", frame_width=w).height / typo.frame_height(w)
        for w in (8.0, 12.0, 30.0, 48.0)
    ]
    # Point sizes land on rasteriser-rounded values, so allow a shade of slop;
    # what matters is that the share does not drift with the shot.
    assert shares == pytest.approx([shares[0]] * len(shares), rel=1e-2)


def test_point_size_scales_with_shot_width():
    assert typo.size_for("body", 24.0) == pytest.approx(
        2 * typo.size_for("body", 12.0), rel=1e-6
    )


def test_scale_is_monotonic_from_display_down_to_micro():
    order = ["display", "title", "heading", "body", "label", "caption", "micro"]
    values = [typo.ROLES[r] for r in order]
    assert values == sorted(values, reverse=True)


def test_every_role_clears_the_readability_floor():
    for role, share in typo.ROLES.items():
        assert share >= typo.MIN_READABLE, f"{role} is below the floor"


def test_unknown_role_names_the_alternatives():
    with pytest.raises(KeyError, match="Roles:"):
        typo.size_for("gigantic", 12.0)


def test_measure_and_audit_flag_unreadable_text():
    """Text sized for a close-up, then judged at the pull-back, must fail."""
    # "Hxy": cap plus descender, so the measured box is comparable to the role's
    # cap-height fraction. A lowercase-only string measures far shorter and
    # would fail the floor at every shot.
    tiny = typo.text("micro", "Hxy", frame_width=6.0)
    assert typo.measure(tiny, 6.0) >= typo.MIN_READABLE, "fine at its own shot"
    assert typo.measure(tiny, 120.0) < typo.MIN_READABLE, "illegible when pulled back"
    assert typo.audit([("tiny", tiny)], 120.0) == ["tiny"]
    assert typo.audit([("tiny", tiny)], 6.0) == []


def test_text_honours_colour_and_mono_face():
    mono = typo.text("body", "abc", frame_width=12.0, mono=True, color=theme.TOKEN)
    assert mono[0].fill_color.to_hex() == theme.TOKEN.to_hex()


# ---------------------------------------------------------------- routing
def _line(*points):
    vm = VMobject()
    vm.set_points_as_corners([np.array(p, dtype=float) for p in points])
    return vm


def test_elbow_is_orthogonal_and_respects_the_first_axis():
    across = routing.elbow([0, 0, 0], [3, 2, 0], first="h")
    assert across[1][1] == pytest.approx(0.0), "h moves in x before y"
    down = routing.elbow([0, 0, 0], [3, 2, 0], first="v")
    assert down[1][0] == pytest.approx(0.0), "v moves in y before x"


def test_elbow_collapses_when_the_route_is_already_straight():
    assert len(routing.elbow([0, 0, 0], [4, 0, 0])) == 2


def test_elbow_rejects_an_unknown_axis():
    with pytest.raises(ValueError):
        routing.elbow([0, 0, 0], [1, 1, 0], first="diagonal")


def test_join_welds_touching_segments_without_duplicating_the_seam():
    joined = routing.join(_line([0, 0, 0], [2, 0, 0]), _line([2, 0, 0], [2, 3, 0]))
    assert joined.point_from_proportion(0.0) == pytest.approx(np.zeros(3), abs=1e-6)
    assert joined.point_from_proportion(1.0) == pytest.approx(
        np.array([2, 3, 0]), abs=1e-6
    )


def test_join_rejects_an_empty_call():
    with pytest.raises(ValueError):
        routing.join()


def test_path_violations_detect_a_line_through_a_box():
    box = Square(side_length=2.0)
    assert not routing.path_clears(_line([-4, 0, 0], [4, 0, 0]), [box])
    around = routing.join(
        routing.elbow([-4, 0, 0], [0, -3, 0], first="v"),
        routing.elbow([0, -3, 0], [4, 0, 0], first="h"),
    )
    assert routing.path_clears(around, [box])


def test_clearance_widens_the_obstacle():
    box = Square(side_length=2.0)
    just_past = _line([-4, 1.2, 0], [4, 1.2, 0])
    assert routing.path_clears(just_past, [box])
    assert not routing.path_clears(just_past, [box], clearance=0.5)


def test_ignore_ends_allows_a_rail_to_terminate_at_a_machine():
    box = Square(side_length=2.0)
    docking = _line([-4, 0, 0], [-0.9, 0, 0])
    assert not routing.path_clears(docking, [box])
    assert routing.path_clears(docking, [box], ignore_ends=0.08)


def test_assert_path_clears_names_the_offender():
    box = Square(side_length=2.0)
    with pytest.raises(AssertionError, match="the model"):
        routing.assert_path_clears(_line([-4, 0, 0], [4, 0, 0]), [("the model", box)])


def test_chord_check_catches_a_corner_the_path_itself_misses():
    """A trail is drawn as straight chords between frames, so a fast corner can
    cut across something the true path goes around."""
    # Tucked into the inside of the corner: the rail goes around it, but a
    # chord drawn straight between two coarse samples slices across it.
    box = Square(side_length=0.6).move_to([2.0, -0.35, 0])
    corner = _line([-3, 0, 0], [2.4, 0, 0], [2.4, -2.4, 0])

    assert routing.path_clears(corner, [box]), "the path itself must miss it"
    assert routing.chord_violations(corner, [box], steps=4), "coarse chords cut it"
    assert not routing.chord_violations(corner, [box], steps=400), "fine chords do not"


def test_assert_trail_clears_reports_the_frame_budget():
    box = Square(side_length=0.6).move_to([2.0, -0.35, 0])
    corner = _line([-3, 0, 0], [2.4, 0, 0], [2.4, -2.4, 0])
    with pytest.raises(AssertionError, match="4 frames"):
        routing.assert_trail_clears(corner, [("a station", box)], steps=4)


def test_bbox_padding():
    left, right, bottom, top = routing.bbox(Square(side_length=2.0), pad=0.5)
    assert (left, right, bottom, top) == pytest.approx((-1.5, 1.5, -1.5, 1.5))
