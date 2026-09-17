#!/usr/bin/env python
"""The Evaluator gate. Nothing is "done" until this exits 0.

PROTECTED FILE (see AGENTS.md → Protected paths). The generator role may not
edit this script, its gates, or the baselines it checks against — an agent that
can edit both the work and its own grading can pass by weakening the check.

Gates, in order (each fails loudly and specifically):

  lint      pyflakes-style compile check of every tracked python file
  import    every module under lib/ and every registered scene imports cleanly
  unit      structural tests for /lib
  snapshot  visual regression against approved baselines
  render    every scene of the target video actually renders at test quality

Usage:
    .venv/bin/python scripts/evaluate.py                     # lib gates only
    .venv/bin/python scripts/evaluate.py --video <slug>      # + that video's scenes
    .venv/bin/python scripts/evaluate.py --video <slug> --scene UserInput
    .venv/bin/python scripts/evaluate.py --skip render       # faster inner loop
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
with open(ROOT / "harness.json") as fh:
    HARNESS = json.load(fh)

PYTHON = str(ROOT / HARNESS["python"])
RENDER_PROFILE = HARNESS["evaluator"]["render_profile"]
RENDER_FLAG = HARNESS["render_profiles"][RENDER_PROFILE]["flag"]


class GateFailure(Exception):
    """Raised with an operator-readable explanation of what failed and where."""


def _run(cmd: list[str], *, cwd: pathlib.Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _python_files() -> list[pathlib.Path]:
    out = []
    for base in ("lib", "videos", "tests", "scripts"):
        out.extend(sorted((ROOT / base).rglob("*.py")))
    return [p for p in out if "__pycache__" not in p.parts]


# ------------------------------------------------------------------ gates
def gate_lint() -> None:
    broken = []
    with tempfile.TemporaryDirectory() as tmp:
        import py_compile

        for path in _python_files():
            cfile = pathlib.Path(tmp) / (path.stem + ".pyc")
            try:
                py_compile.compile(str(path), doraise=True, cfile=str(cfile))
            except py_compile.PyCompileError as exc:
                broken.append(f"{path.relative_to(ROOT)}: {exc.msg.strip()}")
    if broken:
        raise GateFailure("syntax errors:\n  " + "\n  ".join(broken))


def gate_import(video: str | None) -> None:
    modules = [
        f"lib.{p.stem}" if p.parent.name == "lib" else f"lib.components.{p.stem}"
        for p in sorted((ROOT / "lib").rglob("*.py"))
        if p.stem != "__init__"
    ]
    if video:
        for p in sorted((ROOT / "videos" / video / "scenes").glob("*.py")):
            if p.stem != "__init__":
                modules.append(f"videos.{video}.scenes.{p.stem}")
    script = "import importlib\n" + "\n".join(
        f"importlib.import_module({m!r})" for m in modules
    )
    result = _run([PYTHON, "-c", script])
    if result.returncode != 0:
        raise GateFailure(f"import failure:\n{result.stderr.strip()}")


def gate_unit() -> None:
    result = _run(
        [PYTHON, "-m", "pytest", "tests/", "-q",
         "--deselect", "tests/test_components_snapshot.py"]
    )
    if result.returncode != 0:
        raise GateFailure(f"unit tests failed:\n{result.stdout[-4000:]}")


def gate_snapshot() -> None:
    result = _run([PYTHON, "-m", "pytest", "tests/test_components_snapshot.py", "-q"])
    if result.returncode != 0:
        raise GateFailure(
            "visual regression:\n"
            f"{result.stdout[-4000:]}\n"
            "If the change is intentional, LOOK at the render, then run "
            "scripts/approve_baselines.py <case>."
        )


def gate_render(video: str | None, only: str | None) -> None:
    if not video:
        return
    video_dir = ROOT / "videos" / video
    manifest_path = video_dir / "scenes.json"
    if not manifest_path.exists():
        raise GateFailure(f"missing scene manifest: {manifest_path.relative_to(ROOT)}")
    with open(manifest_path) as fh:
        manifest = json.load(fh)

    scenes = [s for s in manifest["scenes"] if not only or s["class"] == only]
    if only and not scenes:
        raise GateFailure(f"no scene named {only!r} in {manifest_path.relative_to(ROOT)}")

    for scene in scenes:
        module_path = video_dir / "scenes" / scene["module"]
        result = _run(
            [PYTHON, "-m", "manim", "render", RENDER_FLAG, "--disable_caching",
             "--media_dir", str(ROOT / "out" / video / "_eval"),
             str(module_path), scene["class"]]
        )
        if result.returncode != 0:
            tail = (result.stderr or result.stdout)[-3000:]
            raise GateFailure(f"scene {scene['class']} failed to render:\n{tail}")


# ------------------------------------------------------------------- main
def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", help="video slug under videos/")
    parser.add_argument("--scene", help="only render this scene class")
    parser.add_argument("--skip", action="append", default=[], help="gate to skip")
    args = parser.parse_args(argv)

    gates = {
        "lint": gate_lint,
        "import": lambda: gate_import(args.video),
        "unit": gate_unit,
        "snapshot": gate_snapshot,
        "render": lambda: gate_render(args.video, args.scene),
    }

    failures = 0
    for name in HARNESS["evaluator"]["gates"]:
        if name in args.skip:
            print(f"[skip] {name}")
            continue
        start = time.time()
        try:
            gates[name]()
        except GateFailure as exc:
            failures += 1
            print(f"[FAIL] {name} ({time.time() - start:.1f}s)\n{exc}\n")
        else:
            print(f"[ok]   {name} ({time.time() - start:.1f}s)")

    if failures:
        print(f"\nEVALUATOR: {failures} gate(s) failed — the work is not done.")
        return 1
    print("\nEVALUATOR: all gates green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
