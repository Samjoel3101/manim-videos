"""Depth and emphasis effects: glow, trails, pulses.

Manim has no gaussian blur, so soft light is faked with concentric stroked
copies whose width grows and whose opacity falls off. It looks better than it
has any right to, and — measured at 1080p60 — it is about four times *cheaper*
to render than compositing a pre-blurred PNG sprite through ``ImageMobject``,
because Cairo's alpha compositing is the bottleneck, not the path count. Layer
count barely moves the cost, so there is no reason to be stingy with it.

What this cannot do is a true soft drop shadow behind a filled card: the trick
only works on strokes. If a design needs real blur, that is an ffmpeg
post-process, not a mobject.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
from manim import (
    Mobject,
    TracedPath,
    VGroup,
    VMobject,
)

from lib import motion, theme

#: Concentric copies per glow. Higher is smoother; cost is near-flat.
GLOW_LAYERS = 12

#: How far the outermost layer extends, in stroke-width units.
GLOW_SPREAD = 1.8

#: Opacity of the innermost glow layer. The falloff is applied from here.
GLOW_OPACITY = 0.17


def glow(
    mobject: VMobject,
    color=None,
    *,
    layers: int = GLOW_LAYERS,
    spread: float = GLOW_SPREAD,
    opacity: float = GLOW_OPACITY,
    falloff: float = 0.6,
) -> VGroup:
    """Concentric stroked copies of ``mobject``, fading outward.

    Returns a group to place *behind* the original. The source mobject is not
    modified. ``falloff`` below 1 concentrates the light near the edge, which
    reads as a glow rather than a fog.
    """
    if layers < 1:
        raise ValueError("glow needs at least one layer")

    color = color or mobject.get_stroke_color()
    halo = VGroup()
    for i in range(layers, 0, -1):
        layer = mobject.copy()
        layer.set_fill(opacity=0)
        layer.set_stroke(
            color=color,
            width=spread * i * theme.STROKE_NORMAL,
            opacity=opacity * (1 - i / layers) ** falloff,
        )
        halo.add(layer)
    return halo


class Glowing(VGroup):
    """A mobject plus its halo, switchable with :meth:`on` and :meth:`off`.

    This is the standard "this station is live" cue for factory videos — it
    replaces thickening a border, which reads as a diagram rather than a machine.
    """

    def __init__(self, mobject: VMobject, color=None, *, start_on: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.core = mobject
        self.glow_color = color or mobject.get_stroke_color()
        self.halo = glow(mobject, self.glow_color, **kwargs.pop("glow_kwargs", {}))
        self.add(self.halo, self.core)  # halo first: it renders behind
        self.halo.set_opacity(1.0 if start_on else 0.0)
        self._on = start_on

    @property
    def is_on(self) -> bool:
        return self._on

    def on(self, intensity: float = 1.0) -> "Glowing":
        # Stroke only. `set_opacity` would also raise the copies' FILL opacity,
        # turning a dozen transparent outlines into a dozen opaque plates that
        # bury whatever the glowing shape contains.
        self.halo.set_stroke(opacity=intensity)
        self._on = intensity > 0
        return self

    def off(self) -> "Glowing":
        self.halo.set_stroke(opacity=0.0)
        self._on = False
        return self

    def dim_glow(self, intensity: float = 0.35) -> "Glowing":
        """Leave a residual glow — "this ran recently" rather than "this is live"."""
        return self.on(intensity)


def comet(
    dot: Mobject,
    *,
    color=None,
    width: float = 6.0,
    dissipating_time: float = 0.35,
) -> TracedPath:
    """A fading trail following ``dot``. Add it to the scene before the dot.

    Follow-through, in animation terms: the trail is what makes a travelling
    packet read as having momentum instead of teleporting frame to frame.
    """
    return TracedPath(
        dot.get_center,
        stroke_color=color or dot.get_color(),
        stroke_width=width,
        dissipating_time=dissipating_time,
    )


def pulse(mobject: Mobject, *, scale: float = 1.06, run_time: float = motion.D_SHORT):
    """One anticipation beat: a small swell and settle.

    Use before the thing actually happens, not after — anticipation is a
    wind-up, and reading it as a reaction is the commonest way to misuse it.
    """
    return mobject.animate(run_time=run_time, rate_func=motion.SHARP).scale(scale).build()


def arrive(node, halo=None, *, scale: float = 1.05, run_time: float = motion.D_SHORT):
    """The "trail lands, node wakes up" beat.

    The idiom this borrows from polished systems-design explainers: a payload
    travels a connector and the machine at the far end reacts on contact, rather
    than every box sitting lit from the first frame. Returns animations to play
    together at the moment of arrival.

    Pass a SHAPE, not a container group. Scaling a ``VGroup`` interpolates the
    group's own rgba — transparent by default — onto its children, so every
    label inside comes out dimmed. This cost a long debugging session; the
    symptom looks like a colour bug, not a grouping one.
    """
    anims = [node.animate(run_time=run_time, rate_func=motion.SNAP).scale(scale).build()]
    if halo is not None:
        anims.append(
            halo.animate(run_time=run_time, rate_func=motion.ENTER)
            .set_stroke(opacity=1.0)
            .build()
        )
    return anims


def settle(node, halo=None, *, scale: float = 1.05, residual: float = 0.3,
           run_time: float = motion.D_SHORT):
    """The other half of :func:`arrive` — undo the pop, leave a residual glow."""
    anims = [
        node.animate(run_time=run_time, rate_func=motion.EXIT).scale(1 / scale).build()
    ]
    if halo is not None:
        anims.append(
            halo.animate(run_time=run_time, rate_func=motion.EXIT)
            .set_stroke(opacity=residual)
            .build()
        )
    return anims


def stack_behind(scene, halo: Mobject, *others: Mobject) -> None:
    """Add ``halo`` to the scene underneath everything given."""
    scene.add(halo)
    scene.bring_to_back(halo)
    for other in others:
        scene.bring_to_front(other)


__all__ = [
    "glow",
    "Glowing",
    "comet",
    "pulse",
    "arrive",
    "settle",
    "stack_behind",
    "GLOW_LAYERS",
    "GLOW_SPREAD",
    "GLOW_OPACITY",
]
