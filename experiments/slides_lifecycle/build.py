#!/usr/bin/env python
"""Render the experimental slides cut and convert it to ONE portable HTML file.

    .venv/bin/python experiments/slides_lifecycle/build.py              # draft, 480p15
    .venv/bin/python experiments/slides_lifecycle/build.py --profile final

The render emits two things from a single pass: the per-slide chunks
manim-slides plays, and an ordinary continuous mp4 (which is what you extract
frames from to review). `manim-slides convert --one-file --offline` then inlines
every chunk and the whole reveal.js runtime into a single self-contained page,
so the deck can be opened from disk with no server and no network.

Nothing here is wired into the Evaluator. This is an experiment.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PYTHON = str(ROOT / ".venv" / "bin" / "python")
SCENE = "SlidesLifecycle"

PROFILES = {
    "draft": {"flag": "-ql", "dir": "480p15"},
    "final": {"flag": "-qh", "dir": "1080p60"},
}


def run(cmd: list[str]) -> None:
    print("  $ " + " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"command failed ({result.returncode}): {' '.join(cmd)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=sorted(PROFILES), default="draft")
    ap.add_argument("--skip-render", action="store_true",
                    help="convert whatever slide config is already on disk")
    args = ap.parse_args()
    profile = PROFILES[args.profile]

    media = ROOT / "out" / "_experiments" / "slides_lifecycle" / args.profile
    dest = media / f"lifecycle_deck_{args.profile}.html"
    media.mkdir(parents=True, exist_ok=True)

    if not args.skip_render:
        run([PYTHON, "-m", "manim", "render", profile["flag"], "--disable_caching",
             "--media_dir", str(media), str(HERE / "slides_scene.py"), SCENE])

    # manim-slides writes its slide config to ./slides/ relative to the CWD.
    config = ROOT / "slides" / f"{SCENE}.json"
    if not config.exists():
        raise SystemExit(f"no slide config at {config} — did the render run?")

    run([PYTHON, "-m", "manim_slides", "convert", SCENE, str(dest),
         "--one-file", "--offline"])

    continuous = media / "videos" / "slides_scene" / profile["dir"] / f"{SCENE}.mp4"
    print(f"\ndeck:       {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")
    print(f"config:     {config}")
    if continuous.exists():
        print(f"continuous: {continuous}")
    else:
        print("continuous: (not found — rendered with --skip-render?)")


if __name__ == "__main__":
    main()
