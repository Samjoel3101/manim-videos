"""Camera choreography contracts.

These matter more than they look: a continuous-shot video is one long camera
move, so an off-by-one in the framing maths is a whole video that clips its
subject rather than one bad frame.
"""

import numpy as np
import pytest
from manim import MovingCameraScene, Scene, VGroup

from lib import camera
from lib.components.factory import Station


class _Moving(MovingCameraScene):
    def construct(self):  # pragma: no cover - never rendered, only constructed
        pass


def _scene():
    scene = _Moving()
    scene.setup()
    return scene


def test_focus_centres_the_frame_on_the_target():
    scene = _scene()
    target = Station("S").shift(np.array([12.0, -3.0, 0.0]))
    anim = camera.focus(scene, target, width=9.0)
    anim.begin()
    anim.interpolate(1.0)
    frame = scene.camera.frame
    assert frame.get_center()[:2] == pytest.approx(target.get_center()[:2], abs=1e-6)
    assert frame.width == pytest.approx(9.0, rel=1e-6)


def test_focus_accepts_an_offset():
    scene = _scene()
    target = Station("S")
    anim = camera.focus(scene, target, width=9.0, shift=np.array([0.0, 2.0, 0.0]))
    anim.begin()
    anim.interpolate(1.0)
    assert scene.camera.frame.get_center()[1] == pytest.approx(2.0, abs=1e-6)


def test_frame_all_fits_every_mobject_with_margin():
    scene = _scene()
    left = Station("A").shift(np.array([-20.0, 0, 0]))
    right = Station("B").shift(np.array([20.0, 0, 0]))
    anim = camera.frame_all(scene, [left, right], pad=2.0)
    anim.begin()
    anim.interpolate(1.0)

    frame = scene.camera.frame
    group = VGroup(left, right)
    assert frame.get_left()[0] <= group.get_left()[0] - 2.0 + 1e-6
    assert frame.get_right()[0] >= group.get_right()[0] + 2.0 - 1e-6
    assert frame.get_bottom()[1] <= group.get_bottom()[1] + 1e-6
    assert frame.get_top()[1] >= group.get_top()[1] - 1e-6


def test_frame_all_is_bound_by_height_when_the_group_is_tall():
    """A tall, narrow group must still fit — width alone would clip it."""
    scene = _scene()
    top = Station("A").shift(np.array([0, 14.0, 0]))
    bottom = Station("B").shift(np.array([0, -14.0, 0]))
    anim = camera.frame_all(scene, [top, bottom], pad=1.0)
    anim.begin()
    anim.interpolate(1.0)

    frame = scene.camera.frame
    assert frame.get_top()[1] >= top.get_top()[1] - 1e-6
    assert frame.get_bottom()[1] <= bottom.get_bottom()[1] + 1e-6


def test_snap_to_moves_the_camera_without_an_animation():
    scene = _scene()
    target = Station("S").shift(np.array([7.0, 1.0, 0]))
    camera.snap_to(scene, target, width=8.0)
    assert scene.camera.frame.width == pytest.approx(8.0, rel=1e-6)
    assert scene.camera.frame.get_center()[0] == pytest.approx(7.0, abs=1e-6)


def test_camera_helpers_reject_a_fixed_camera_scene():
    """A plain Scene has no movable frame — fail with a readable message."""
    scene = Scene()
    scene.setup()
    with pytest.raises(TypeError, match="MovingCameraScene"):
        camera.focus(scene, Station("S"), width=9.0)
