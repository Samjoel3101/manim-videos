"""Reusable scene-level transitions.

These return animations (or run on a scene) so pacing is consistent between
videos. Durations come from ``lib.theme`` — don't pass raw numbers from a scene
unless a beat genuinely needs to differ.
"""

from __future__ import annotations

from typing import Sequence

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AnimationGroup,
    FadeIn,
    FadeOut,
    Mobject,
    Scene,
    Succession,
    VGroup,
    Write,
)

from lib import theme
from lib import utils


def title_card(
    scene: Scene,
    title: str,
    subtitle: str | None = None,
    *,
    hold: float = theme.T_SLOW,
) -> None:
    """Write a centred title (optionally with a subtitle), hold, then clear."""
    title_mob = utils.heading(title)
    group = VGroup(title_mob)
    if subtitle:
        group.add(utils.label(subtitle))
        group.arrange(DOWN, buff=theme.PAD_MD)
    group.move_to([0, 0, 0])

    scene.play(Write(title_mob), run_time=theme.T_NORMAL)
    if subtitle:
        scene.play(FadeIn(group[1], shift=UP * theme.PAD_SM), run_time=theme.T_FAST)
    scene.wait(hold)
    scene.play(FadeOut(group), run_time=theme.T_FAST)


def fade_through(
    scene: Scene,
    out_mobjects: Sequence[Mobject],
    in_mobjects: Sequence[Mobject],
    *,
    run_time: float = theme.T_NORMAL,
) -> None:
    """Cross-fade one set of mobjects out and another in, overlapping slightly."""
    anims = []
    if out_mobjects:
        anims.append(AnimationGroup(*[FadeOut(m) for m in out_mobjects]))
    if in_mobjects:
        anims.append(AnimationGroup(*[FadeIn(m) for m in in_mobjects]))
    if not anims:
        return
    scene.play(Succession(*anims, lag_ratio=0.6), run_time=run_time)


def slide_swap(
    scene: Scene,
    outgoing: Mobject,
    incoming: Mobject,
    *,
    direction=LEFT,
    run_time: float = theme.T_NORMAL,
) -> None:
    """Push ``outgoing`` off-frame while ``incoming`` slides in behind it."""
    fw, _ = utils.frame_bounds()
    offset = direction * fw
    incoming.shift(-offset)
    scene.play(
        outgoing.animate.shift(offset),
        incoming.animate.shift(offset),
        run_time=run_time,
    )


def focus_on(
    scene: Scene,
    target: Mobject,
    others: Sequence[Mobject],
    *,
    dim: float = 0.25,
    run_time: float = theme.T_FAST,
) -> None:
    """Dim everything but ``target`` — the standard "look here" beat."""
    scene.play(
        *[m.animate.set_opacity(dim) for m in others if m is not target],
        target.animate.set_opacity(1.0),
        run_time=run_time,
    )


def undim(scene: Scene, mobjects: Sequence[Mobject], *, run_time: float = theme.T_FAST) -> None:
    """Undo :func:`focus_on`."""
    scene.play(*[m.animate.set_opacity(1.0) for m in mobjects], run_time=run_time)


def clear_scene(scene: Scene, *, run_time: float = theme.T_FAST) -> None:
    """Fade out everything currently on screen. Use between major beats."""
    if scene.mobjects:
        scene.play(*[FadeOut(m) for m in scene.mobjects], run_time=run_time)


__all__ = ["title_card", "fade_through", "slide_swap", "focus_on", "undim", "clear_scene"]
