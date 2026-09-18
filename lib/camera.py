"""Camera choreography for continuous-shot videos.

A "factory tour" video never cuts: one set is built once and the camera flies
around it. These helpers wrap the frame arithmetic so scenes describe intent
("focus on the tokenizer at width 9") instead of computing frame rectangles.

All of these require a ``MovingCameraScene`` (or any scene whose camera exposes
a ``frame``); they raise a clear error rather than failing obscurely if not.
"""

from __future__ import annotations

from typing import Iterable

from manim import Mobject, VGroup

from lib import theme


def _frame(scene):
    frame = getattr(scene.camera, "frame", None)
    if frame is None:
        raise TypeError(
            f"{type(scene).__name__} has no movable camera frame — "
            "a continuous-shot scene must subclass MovingCameraScene."
        )
    return frame


def focus(
    scene,
    target: Mobject,
    *,
    width: float,
    run_time: float = theme.T_NORMAL,
    shift=None,
):
    """Animation moving the camera to centre ``target`` at the given frame width.

    Returns a built ``Animation`` rather than playing it, so a scene can run the
    camera move *simultaneously* with the action at its destination — which is
    what keeps a continuous shot feeling continuous rather than stop-and-go.
    """
    frame = _frame(scene)
    centre = target.get_center() if shift is None else target.get_center() + shift
    return (
        frame.animate(run_time=run_time).move_to(centre).set(width=width).build()
    )


def frame_all(
    scene,
    mobjects: Iterable[Mobject],
    *,
    pad: float = 2.0,
    run_time: float = theme.T_SLOW,
):
    """Animation pulling the camera back until everything given is in shot.

    ``pad`` is extra world-space margin on each side. The width is chosen from
    whichever dimension binds, so the result fits both axes at 16:9.
    """
    frame = _frame(scene)
    group = VGroup(*mobjects)
    aspect = frame.width / frame.height

    needed_width = group.width + 2 * pad
    needed_from_height = (group.height + 2 * pad) * aspect
    width = max(needed_width, needed_from_height)

    return (
        frame.animate(run_time=run_time)
        .move_to(group.get_center())
        .set(width=width)
        .build()
    )


def snap_to(scene, target: Mobject, *, width: float) -> None:
    """Place the camera instantly, with no animation. For the opening frame."""
    _frame(scene).move_to(target.get_center()).set(width=width)


__all__ = ["focus", "frame_all", "snap_to"]
