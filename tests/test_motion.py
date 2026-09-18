"""The motion language's contracts.

Easing bugs are insidious: a curve that overshoots or runs backwards produces a
video that looks subtly broken in a way no still frame shows. These are cheap
and they pin the behaviour down.
"""

import numpy as np
import pytest

from lib import motion


SAMPLES = np.linspace(0.0, 1.0, 101)
CURVES = {
    name: getattr(motion, name)
    for name in ("STANDARD", "DECELERATE", "ACCELERATE", "SHARP", "EMPHASIZED")
}


@pytest.mark.parametrize("name", sorted(CURVES))
def test_curve_starts_at_zero_and_ends_at_one(name):
    curve = CURVES[name]
    assert curve(0.0) == pytest.approx(0.0, abs=1e-9)
    assert curve(1.0) == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("name", sorted(CURVES))
def test_curve_is_monotonic(name):
    """A rate function that goes backwards makes the animation stutter."""
    values = [CURVES[name](a) for a in SAMPLES]
    assert all(b >= a - 1e-9 for a, b in zip(values, values[1:]))


@pytest.mark.parametrize("name", sorted(CURVES))
def test_curve_stays_in_range(name):
    """None of these curves is meant to overshoot — that is a different look."""
    values = [CURVES[name](a) for a in SAMPLES]
    assert min(values) >= -1e-9
    assert max(values) <= 1 + 1e-9


@pytest.mark.parametrize("name", sorted(CURVES))
def test_curve_clamps_out_of_range_input(name):
    curve = CURVES[name]
    assert curve(-0.5) == pytest.approx(0.0, abs=1e-9)
    assert curve(1.5) == pytest.approx(1.0, abs=1e-9)


def test_linear_bezier_is_the_identity():
    """cubic-bezier(0,0,1,1) is linear — a sanity check on the solver itself."""
    linear = motion.cubic_bezier_rate(0.0, 0.0, 1.0, 1.0)
    for a in SAMPLES:
        assert linear(a) == pytest.approx(a, abs=2e-3)


def test_decelerate_front_loads_and_accelerate_back_loads():
    """The whole point of the pair: they must be distinguishable at the midpoint."""
    assert motion.DECELERATE(0.5) > 0.5, "entering elements cover ground early"
    assert motion.ACCELERATE(0.5) < 0.5, "exiting elements cover ground late"


def test_sharp_is_roughly_symmetric():
    assert motion.SHARP(0.5) == pytest.approx(0.5, abs=0.05)


def test_semantic_aliases_point_at_real_curves():
    assert motion.ENTER is motion.DECELERATE
    assert motion.EXIT is motion.ACCELERATE
    assert motion.MOVE is motion.STANDARD


def test_duration_scales_with_distance_but_sub_linearly():
    near = motion.duration_for(3.0)
    far = motion.duration_for(12.0)
    assert far > near, "longer moves take longer"
    assert far < near * 4, "but not proportionally, or crossing the set drags"


def test_duration_is_clamped_at_both_ends():
    assert motion.duration_for(0.0) == pytest.approx(motion.D_SHORT)
    assert motion.duration_for(1e6) == pytest.approx(motion.D_EXTRA)
    assert motion.duration_for(-5) == pytest.approx(motion.D_SHORT)


def test_travel_time_uses_straight_line_distance():
    a, b = np.array([0.0, 0, 0]), np.array([3.0, 4.0, 0])
    assert motion.travel_time(a, b) == pytest.approx(motion.duration_for(5.0))


def test_exits_are_quicker_than_entrances():
    assert motion.EXIT_FACTOR < 1.0


def test_enter_and_leave_build_staggered_animations():
    from manim import Dot

    dots = [Dot() for _ in range(4)]
    grouped = motion.enter(dots)
    assert len(grouped.animations) == 4
    assert grouped.lag_ratio > 0, "a group arriving on one frame reads as a slide"
    assert motion.leave(dots).lag_ratio < grouped.lag_ratio, "exits are tighter"
