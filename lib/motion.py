"""The motion language: easing curves, durations, and the rules for picking them.

`theme.py` decides what the series looks like; this decides how it *moves*. Both
exist for the same reason — a back catalogue only feels like one series if these
choices are made once, centrally, rather than re-guessed per scene.

The curves are the Material Design motion set, implemented as real cubic-Béziers
rather than approximated with Manim's named rate functions, so they match the
published values exactly. The durations follow the standard UI-motion guidance
those systems and NN/g converge on:

* **entering** elements decelerate into place — 200–300ms
* **exiting** elements accelerate away — 150–200ms, faster than entering, because
  the viewer has already stopped caring about them
* **on-screen movement** uses the standard ease-in-out — 200–500ms
* duration scales with the distance travelled; one duration for every move makes
  short hops feel sluggish and long ones feel rushed

Explainer video is not UI, so these are floors rather than targets: a beat the
viewer has to *read* is held longer than a button that just has to feel
responsive. Use `theme.T_*` for narrative holds and this module for the motion
inside them.
"""

from __future__ import annotations

from typing import Callable, Iterable, Sequence

import numpy as np
from manim import AnimationGroup, FadeIn, FadeOut, LaggedStart, Mobject

from lib import theme


# --------------------------------------------------------------------------
# Cubic-Bézier easing
# --------------------------------------------------------------------------
def cubic_bezier_rate(x1: float, y1: float, x2: float, y2: float) -> Callable[[float], float]:
    """Build a Manim rate function from CSS ``cubic-bezier(x1, y1, x2, y2)``.

    The curve is defined with time on x and progress on y, so evaluating it means
    solving for the ``t`` that gives a particular x, then reading y. Newton's
    method converges in a handful of iterations over [0, 1]; the bisection
    fallback covers the near-vertical curves where Newton can stall.
    """

    def _curve(a: float, b: float, t: float) -> float:
        # Cubic Bézier with implicit endpoints at 0 and 1.
        return 3 * a * (1 - t) ** 2 * t + 3 * b * (1 - t) * t**2 + t**3

    def _slope(a: float, b: float, t: float) -> float:
        return (
            3 * a * (1 - 4 * t + 3 * t**2)
            + 3 * b * (2 * t - 3 * t**2)
            + 3 * t**2
        )

    def rate(alpha: float) -> float:
        alpha = min(1.0, max(0.0, float(alpha)))
        if alpha in (0.0, 1.0):
            return alpha

        t = alpha
        for _ in range(8):
            error = _curve(x1, x2, t) - alpha
            if abs(error) < 1e-6:
                return _curve(y1, y2, t)
            derivative = _slope(x1, x2, t)
            if abs(derivative) < 1e-6:
                break
            t -= error / derivative

        low, high = 0.0, 1.0
        t = alpha
        for _ in range(24):
            if _curve(x1, x2, t) < alpha:
                low = t
            else:
                high = t
            t = (low + high) / 2
        return _curve(y1, y2, t)

    return rate


#: Movement between two on-screen positions. The default for anything that is
#: already visible and is going somewhere else.
STANDARD = cubic_bezier_rate(0.4, 0.0, 0.2, 1.0)

#: Entering the frame: full velocity at the start, settling at the end.
DECELERATE = cubic_bezier_rate(0.0, 0.0, 0.2, 1.0)

#: Leaving the frame: starts still, accelerates away, never comes back.
ACCELERATE = cubic_bezier_rate(0.4, 0.0, 1.0, 1.0)

#: Quick, non-committal moves that stay on screen — a dismiss, a small nudge.
SHARP = cubic_bezier_rate(0.4, 0.0, 0.6, 1.0)

#: For the one move per beat that should draw the eye. More dramatic
#: acceleration and a longer settle; used sparingly or it stops being emphatic.
EMPHASIZED = cubic_bezier_rate(0.2, 0.0, 0.0, 1.0)

#: Semantic aliases. Prefer these at call sites — they say *why*, and the curve
#: behind them can be retuned series-wide without touching a single scene.
ENTER = DECELERATE
EXIT = ACCELERATE
MOVE = STANDARD
SNAP = SHARP
FEATURE = EMPHASIZED


# --------------------------------------------------------------------------
# Durations
# --------------------------------------------------------------------------
#: Named durations in seconds. Shorter than the narrative beats in `theme`,
#: because these describe a single movement, not a section of the film.
D_INSTANT = 0.12
D_SHORT = 0.20
D_MEDIUM = 0.32
D_LONG = 0.50
D_EXTRA = 0.75

#: Exits are quicker than entrances — the viewer is done with the thing.
EXIT_FACTOR = 0.7

#: Distance, in Manim units, that `duration_for` treats as a "typical" move.
REFERENCE_DISTANCE = 6.0


def duration_for(
    distance: float,
    *,
    base: float = D_MEDIUM,
    minimum: float = D_SHORT,
    maximum: float = D_EXTRA,
) -> float:
    """Duration for a move of ``distance`` units, scaled sub-linearly.

    A square-root relationship, not a linear one: doubling the distance should
    make a move somewhat longer, not twice as long, or crossing the factory
    floor takes an age. Clamped at both ends so nothing is instant or glacial.
    """
    if distance <= 0:
        return minimum
    scaled = base * float(np.sqrt(distance / REFERENCE_DISTANCE))
    return float(min(maximum, max(minimum, scaled)))


def travel_time(start, end, **kwargs) -> float:
    """``duration_for`` the straight-line distance between two points."""
    return duration_for(float(np.linalg.norm(np.array(end) - np.array(start))), **kwargs)


# --------------------------------------------------------------------------
# Stagger
# --------------------------------------------------------------------------
#: Default lag between staggered siblings. Enough to read as a sequence, small
#: enough that the group still arrives as one gesture.
LAG = 0.15


def enter(mobjects: Iterable[Mobject], *, shift=None, scale: float = 0.94, lag: float = LAG):
    """Staggered entrance: the group arrives as a wave, not a wall.

    Leading the eye through a group in order is what "stagger and lag" buys you;
    every element appearing on the same frame reads as a static slide.
    """
    items = list(mobjects)
    shift = np.array([0.0, theme.PAD_SM, 0.0]) if shift is None else np.asarray(shift)
    return LaggedStart(
        *[FadeIn(m, shift=shift, scale=scale) for m in items],
        lag_ratio=lag,
    )


def leave(mobjects: Iterable[Mobject], *, shift=None, lag: float = LAG * 0.6):
    """Staggered exit. Faster and flatter than the entrance, by design."""
    items = list(mobjects)
    shift = np.array([0.0, -theme.PAD_XS, 0.0]) if shift is None else np.asarray(shift)
    return LaggedStart(*[FadeOut(m, shift=shift) for m in items], lag_ratio=lag)


def together(*animations, lag: float = 0.0):
    """Play animations as one gesture, optionally with a little overlap."""
    return AnimationGroup(*animations, lag_ratio=lag)


__all__ = [
    "cubic_bezier_rate",
    "STANDARD",
    "DECELERATE",
    "ACCELERATE",
    "SHARP",
    "EMPHASIZED",
    "ENTER",
    "EXIT",
    "MOVE",
    "SNAP",
    "FEATURE",
    "D_INSTANT",
    "D_SHORT",
    "D_MEDIUM",
    "D_LONG",
    "D_EXTRA",
    "EXIT_FACTOR",
    "duration_for",
    "travel_time",
    "LAG",
    "enter",
    "leave",
    "together",
]
