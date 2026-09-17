#!/usr/bin/env python
"""Render every scene of "What happens when you send a message to ChatGPT" in order and concatenate to one file.

Usage:
    .venv/bin/python videos/chatgpt_message_journey/render.py               # default profile
    .venv/bin/python videos/chatgpt_message_journey/render.py --profile final
    .venv/bin/python videos/chatgpt_message_journey/render.py --scene UserInput --no-concat
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SLUG = HERE.name

with open(ROOT / "harness.json") as fh:
    HARNESS = json.load(fh)
with open(HERE / "scenes.json") as fh:
    MANIFEST = json.load(fh)

PYTHON = str(ROOT / HARNESS["python"])


def render_scene(scene: dict, profile: dict, media_dir: pathlib.Path) -> pathlib.Path:
    module = HERE / "scenes" / scene["module"]
    cmd = [
        PYTHON, "-m", "manim", "render", profile["flag"], "--disable_caching",
        "--media_dir", str(media_dir), str(module), scene["class"],
    ]
    print(f"  rendering {scene['class']} …", flush=True)
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            f"render failed for {scene['class']}:\n{(result.stderr or result.stdout)[-3000:]}"
        )
    out = media_dir / "videos" / module.stem / profile["dir"] / f"{scene['class']}.mp4"
    if not out.exists():
        raise SystemExit(f"expected output missing: {out}")
    return out


def concat(parts: list[pathlib.Path], dest: pathlib.Path) -> None:
    """Stream-copy concat via ffmpeg. All parts share a profile, so no re-encode."""
    listing = dest.parent / "_concat.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts))
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
           "-c", "copy", str(dest)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"ffmpeg concat failed:\n{result.stderr[-3000:]}")
    listing.unlink(missing_ok=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=HARNESS["default_profile"],
                        choices=sorted(HARNESS["render_profiles"]))
    parser.add_argument("--scene", help="render only this scene class")
    parser.add_argument("--no-concat", action="store_true")
    args = parser.parse_args(argv)

    profile = HARNESS["render_profiles"][args.profile]
    media_dir = ROOT / HARNESS["paths"]["output"] / SLUG / args.profile
    media_dir.mkdir(parents=True, exist_ok=True)

    scenes = [s for s in MANIFEST["scenes"] if s.get("status") != "planned"]
    if args.scene:
        scenes = [s for s in MANIFEST["scenes"] if s["class"] == args.scene]
        if not scenes:
            raise SystemExit(f"no scene named {args.scene!r} in scenes.json")

    if not scenes:
        raise SystemExit("nothing to render — every scene is still 'planned'")

    print(f"{MANIFEST['title']} — {len(scenes)} scene(s) at {args.profile}")
    parts = [render_scene(s, profile, media_dir) for s in scenes]

    if args.no_concat or len(parts) == 1:
        for p in parts:
            print(f"  -> {p}")
        return 0

    dest = media_dir / f"{SLUG}_{args.profile}.mp4"
    concat(parts, dest)
    print(f"\nfinal cut: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
