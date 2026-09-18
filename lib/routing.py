"""Path geometry: orthogonal routes, joining rails, and clearance checking.

A travelling payload must follow the rails the viewer can see. The bug this
module exists to prevent is the one that shipped: the end-of-film loop was built
as a fresh polyline through station *centres*, so the token flew straight
through solid boxes while the drawn rails went around them.

The fix is structural rather than a nudge — :func:`join` builds the travel path
*out of the rails themselves*, so the two cannot disagree — plus
:func:`path_clears`, a predicate a set can assert on itself at construction, so
a routing regression fails the render gate instead of shipping.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
from manim import Mobject, VMobject

#: Sample count when testing a path against obstacles. Dense enough to catch a
#: clipped corner, cheap enough to run on every construction.
CLEARANCE_SAMPLES = 400


def as_points(obj) -> list[np.ndarray]:
    """Corner points of a rail, a raw point list, or anything path-like."""
    if hasattr(obj, "path"):  # a Conveyor
        obj = obj.path
    if isinstance(obj, VMobject):
        return [np.array(p, dtype=float) for p in obj.get_anchors()]
    return [np.array(p, dtype=float) for p in obj]


def elbow(start, end, *, first: str = "h") -> list[np.ndarray]:
    """Two-segment orthogonal route from ``start`` to ``end``.

    ``first`` picks which axis moves first: ``"h"`` goes across then down,
    ``"v"`` goes down then across. Diagonal rails read as sloppy in a diagram
    style, so everything between machines should be one of these.
    """
    start = np.array(start, dtype=float)
    end = np.array(end, dtype=float)
    if first not in ("h", "v"):
        raise ValueError("first must be 'h' or 'v'")
    corner = (
        np.array([end[0], start[1], 0.0])
        if first == "h"
        else np.array([start[0], end[1], 0.0])
    )
    points = [start, corner, end]
    # Collapse the corner when the route is already straight.
    return [p for i, p in enumerate(points) if i == 0 or not np.allclose(p, points[i - 1])]


def join(*segments, tolerance: float = 0.35) -> VMobject:
    """Concatenate rails into one continuous path for ``MoveAlongPath``.

    Accepts ``Conveyor`` objects, ``VMobject`` paths, or raw point lists, in
    travel order. Consecutive segments whose ends are within ``tolerance`` are
    welded; a larger gap is bridged with a straight run rather than silently
    teleporting the payload.
    """
    if not segments:
        raise ValueError("join needs at least one segment")

    points: list[np.ndarray] = []
    for segment in segments:
        pts = as_points(segment)
        if not pts:
            continue
        if points and np.linalg.norm(pts[0] - points[-1]) <= tolerance:
            pts = pts[1:]  # weld: drop the duplicated join point
        points.extend(pts)

    deduped: list[np.ndarray] = []
    for p in points:
        if not deduped or not np.allclose(p, deduped[-1]):
            deduped.append(p)
    if len(deduped) < 2:
        raise ValueError("joined path collapsed to a single point")

    path = VMobject()
    path.set_points_as_corners(deduped)
    return path


def bbox(mobject: Mobject, *, pad: float = 0.0) -> tuple[float, float, float, float]:
    """``(left, right, bottom, top)`` of a mobject, optionally grown by ``pad``."""
    return (
        float(mobject.get_left()[0]) - pad,
        float(mobject.get_right()[0]) + pad,
        float(mobject.get_bottom()[1]) - pad,
        float(mobject.get_top()[1]) + pad,
    )


def _inside(point, box) -> bool:
    left, right, bottom, top = box
    return left <= point[0] <= right and bottom <= point[1] <= top


def path_violations(
    path,
    obstacles: Iterable[Mobject],
    *,
    clearance: float = 0.0,
    samples: int = CLEARANCE_SAMPLES,
    ignore_ends: float = 0.0,
) -> list[int]:
    """Indices of ``obstacles`` the path passes through.

    ``ignore_ends`` excludes a fraction of the path at each end, for the common
    legitimate case of a rail that deliberately terminates *at* a machine.
    """
    boxes = [bbox(o, pad=clearance) for o in obstacles]
    hits: set[int] = set()

    vm = path
    if hasattr(vm, "path"):
        vm = vm.path
    if not isinstance(vm, VMobject):
        vm = join(vm)

    lo, hi = ignore_ends, 1.0 - ignore_ends
    for i in range(samples + 1):
        alpha = i / samples
        if alpha < lo or alpha > hi:
            continue
        point = vm.point_from_proportion(alpha)
        for index, box in enumerate(boxes):
            if _inside(point, box):
                hits.add(index)
    return sorted(hits)


def chord_violations(
    path,
    obstacles: Iterable[Mobject],
    *,
    steps: int,
    clearance: float = 0.0,
    resolution: int = 12,
) -> list[int]:
    """Obstacles hit by the *straight chords* a trail actually draws.

    A comet trail is sampled once per frame and joined with straight segments,
    so on a fast corner it cuts the corner — the drawn trail leaves the rail even
    though the underlying path never does. :func:`path_violations` cannot see
    this, because it walks the true curve.

    ``steps`` is the number of frames the traversal takes: ``fps * run_time``.
    Fewer frames means longer chords means more corner-cutting, so a fast loop
    needs either more clearance or more time.
    """
    vm = path
    if hasattr(vm, "path"):
        vm = vm.path
    if not isinstance(vm, VMobject):
        vm = join(vm)

    boxes = [bbox(o, pad=clearance) for o in obstacles]
    hits: set[int] = set()
    samples = [vm.point_from_proportion(i / steps) for i in range(steps + 1)]

    for start, end in zip(samples, samples[1:]):
        for t in range(resolution + 1):
            point = start + (end - start) * (t / resolution)
            for index, box in enumerate(boxes):
                if _inside(point, box):
                    hits.add(index)
    return sorted(hits)


def assert_trail_clears(
    path,
    named_obstacles: Sequence[tuple[str, Mobject]],
    *,
    steps: int,
    **kwargs,
) -> None:
    """Raise if the chords a trail draws would cross an obstacle."""
    names = [n for n, _ in named_obstacles]
    mobs = [m for _, m in named_obstacles]
    bad = chord_violations(path, mobs, steps=steps, **kwargs)
    if bad:
        raise AssertionError(
            "trail chords cut across: "
            + ", ".join(names[i] for i in bad)
            + f" at {steps} frames. Slow the traversal, or move the rail "
            "further from the obstacle so a corner chord cannot reach it."
        )


def path_clears(path, obstacles: Iterable[Mobject], **kwargs) -> bool:
    """True if the path passes through none of the obstacles."""
    return not path_violations(path, obstacles, **kwargs)


def assert_path_clears(path, named_obstacles: Sequence[tuple[str, Mobject]], **kwargs) -> None:
    """Raise with the offending names if a path crosses any obstacle.

    Call this from a set's constructor. A trail that cuts through a machine is a
    geometry bug, and geometry bugs should fail loudly at build time rather than
    be discovered in a render three minutes later.
    """
    names = [n for n, _ in named_obstacles]
    mobs = [m for _, m in named_obstacles]
    bad = path_violations(path, mobs, **kwargs)
    if bad:
        raise AssertionError(
            "travel path passes through: "
            + ", ".join(names[i] for i in bad)
            + ". Build the path by joining the drawn rails (lib.routing.join) "
            "rather than connecting centres."
        )


__all__ = [
    "as_points",
    "elbow",
    "join",
    "bbox",
    "path_violations",
    "path_clears",
    "assert_path_clears",
    "chord_violations",
    "assert_trail_clears",
    "CLEARANCE_SAMPLES",
]
