"""Shared test machinery for /lib visual regression.

PROTECTED FILE. This is the evaluation side of the harness: the generator role
must not edit it to make a failing component pass. Changes here go through a
human. See AGENTS.md → "Protected paths".

Two tiers of check are provided:

* **structural** — cheap assertions on a constructed mobject (size, frame
  safety, submobject counts, theme colours). Fast, deterministic, no rendering.
* **snapshot** — render one frame and compare a downsampled perceptual
  signature against a stored baseline. Catches "it still constructs but now
  looks wrong", which structural checks cannot see.

Known blind spot, stated rather than implied: a snapshot signature compares a
16x16 luminance grid, so it catches layout/shape/contrast regressions but NOT
small colour shifts or single-glyph typos. Those need human spot-checking.
"""

from __future__ import annotations

import json
import pathlib
from typing import Callable

import numpy as np
import pytest
from manim import Mobject, Scene, tempconfig

from lib import theme, utils

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASELINE_DIR = ROOT / "tests" / "baselines"
ARTIFACT_DIR = ROOT / "tests" / "_artifacts"

#: Grid resolution of the perceptual signature.
GRID = 16

with open(ROOT / "harness.json") as fh:
    HARNESS = json.load(fh)

TOLERANCE = float(HARNESS["evaluator"]["snapshot_tolerance"])


class _ComponentScene(Scene):
    """Renders exactly one mobject on the themed background, centred."""

    factory: Callable[[], Mobject]

    def construct(self) -> None:
        theme.apply(self)
        mob = type(self).factory()
        mob.move_to([0, 0, 0])
        self.add(mob)


def render_frame(factory: Callable[[], Mobject]) -> np.ndarray:
    """Render ``factory()`` to a single RGBA frame at test quality."""
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    scene_cls = type("_Snap", (_ComponentScene,), {"factory": staticmethod(factory)})
    with tempconfig(
        {
            "quality": "low_quality",
            "disable_caching": True,
            "write_to_movie": False,
            "format": "png",
            "save_last_frame": True,
            "media_dir": str(ARTIFACT_DIR),
            "verbosity": "ERROR",
            "background_color": theme.BG,
        }
    ):
        scene = scene_cls()
        scene.render()
        return scene.renderer.get_frame()


def signature(frame: np.ndarray, grid: int = GRID) -> list[float]:
    """Downsample a frame to a ``grid x grid`` normalised luminance signature."""
    rgb = frame[:, :, :3].astype(np.float64)
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    h, w = lum.shape
    rows = np.array_split(np.arange(h), grid)
    cols = np.array_split(np.arange(w), grid)
    out = []
    for r in rows:
        for c in cols:
            out.append(float(lum[np.ix_(r, c)].mean()) / 255.0)
    return out


def baseline_path(name: str) -> pathlib.Path:
    return BASELINE_DIR / f"{name}.json"


def load_baseline(name: str) -> list[float] | None:
    path = baseline_path(name)
    if not path.exists():
        return None
    with open(path) as fh:
        return json.load(fh)["signature"]


def drift(a: list[float], b: list[float]) -> float:
    """Mean absolute difference between two signatures, in [0, 1]."""
    if len(a) != len(b):
        return 1.0
    return float(np.mean(np.abs(np.array(a) - np.array(b))))


@pytest.fixture(scope="session")
def snapshot():
    """``snapshot(name, factory)`` — assert a component matches its baseline.

    A missing baseline FAILS rather than silently self-approving; run
    ``python scripts/approve_baselines.py`` (a deliberate, reviewable act) to
    record one.
    """

    def _check(name: str, factory: Callable[[], Mobject]) -> None:
        expected = load_baseline(name)
        actual = signature(render_frame(factory))
        if expected is None:
            pytest.fail(
                f"No baseline for '{name}'. Inspect the component, then run:\n"
                f"  .venv/bin/python scripts/approve_baselines.py {name}"
            )
        d = drift(expected, actual)
        assert d <= TOLERANCE, (
            f"Visual regression in '{name}': drift {d:.4f} > tolerance {TOLERANCE}. "
            f"If this change is intended, re-approve the baseline explicitly."
        )

    return _check


@pytest.fixture
def in_frame():
    """``in_frame(mobject)`` — assert the mobject fits the 16:9 safe area."""

    def _check(mob: Mobject) -> None:
        mob.move_to([0, 0, 0])
        assert utils.is_in_frame(mob), (
            f"Component overflows the safe area: "
            f"{mob.width:.2f}x{mob.height:.2f} vs frame "
            f"{utils.frame_bounds()[0]:.2f}x{utils.frame_bounds()[1]:.2f}"
        )

    return _check
