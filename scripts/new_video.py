#!/usr/bin/env python
"""Scaffold a new video project with the per-project harness files in place.

Setup phase, run once per video. Creates the folder, the per-video AGENTS.md,
an empty feature list, a progress log, a scene manifest and a render driver, so
a steady-state session never has to re-derive the structure.

Usage:
    .venv/bin/python scripts/new_video.py chatgpt_message_journey \\
        --title "What happens when you send a message to ChatGPT"

Slugs are python-identifier-shaped (underscores, not hyphens) because the
Evaluator imports scene modules by dotted path.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

AGENTS_TEMPLATE = """# {title}

Video project. Read the root `AGENTS.md` first — it governs /lib and the
promotion rule. This file covers only what is specific to this video.

## Where things are

- `script.md` — narration and beat timings. The source of truth for pacing.
- `feature_list.json` — one entry per scene. Status flags live here, not in prose.
- `claude-progress.txt` — what the last session did, tried, and left broken.
- `scenes.json` — the render manifest: scene order, module, duration budget.
- `scenes/` — one module per scene. Import from `/lib`; keep one-offs local.
- `render.py` — renders every scene in manifest order and concatenates.

## Working on this video

1. `./init.sh` from the repo root.
2. Read `claude-progress.txt`, then `feature_list.json`; take the highest-priority
   `failing` scene, not the easiest one.
3. Build the scene. Reuse `/lib` components; promote a local one only under the
   root AGENTS.md rule.
4. `.venv/bin/python scripts/evaluate.py --video {slug} --scene <SceneClass>`
5. Only when that is green, flip the scene's status in `feature_list.json` and
   append to `claude-progress.txt`.

## Visual conventions for this video

_(fill in: recurring colours, camera framing, any motif this video repeats)_
"""

RENDER_TEMPLATE = '''#!/usr/bin/env python
"""Render every scene of "{title}" in order and concatenate to one file.

Usage:
    .venv/bin/python videos/{slug}/render.py               # default profile
    .venv/bin/python videos/{slug}/render.py --profile final
    .venv/bin/python videos/{slug}/render.py --scene UserInput --no-concat
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
    print(f"  rendering {{scene['class']}} …", flush=True)
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            f"render failed for {{scene['class']}}:\\n{{(result.stderr or result.stdout)[-3000:]}}"
        )
    out = media_dir / "videos" / module.stem / profile["dir"] / f"{{scene['class']}}.mp4"
    if not out.exists():
        raise SystemExit(f"expected output missing: {{out}}")
    return out


def concat(parts: list[pathlib.Path], dest: pathlib.Path) -> None:
    """Stream-copy concat via ffmpeg. All parts share a profile, so no re-encode."""
    listing = dest.parent / "_concat.txt"
    listing.write_text("".join(f"file '{{p}}'\\n" for p in parts))
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
           "-c", "copy", str(dest)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"ffmpeg concat failed:\\n{{result.stderr[-3000:]}}")
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
            raise SystemExit(f"no scene named {{args.scene!r}} in scenes.json")

    if not scenes:
        raise SystemExit("nothing to render — every scene is still 'planned'")

    print(f"{{MANIFEST['title']}} — {{len(scenes)}} scene(s) at {{args.profile}}")
    parts = [render_scene(s, profile, media_dir) for s in scenes]

    if args.no_concat or len(parts) == 1:
        for p in parts:
            print(f"  -> {{p}}")
        return 0

    dest = media_dir / f"{{SLUG}}_{{args.profile}}.mp4"
    concat(parts, dest)
    print(f"\\nfinal cut: {{dest}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
'''


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="python-identifier-shaped folder name")
    parser.add_argument("--title", required=True)
    args = parser.parse_args(argv)

    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.slug):
        print("slug must be lowercase letters, digits and underscores")
        return 2

    video_dir = ROOT / "videos" / args.slug
    if video_dir.exists():
        print(f"{video_dir.relative_to(ROOT)} already exists")
        return 2

    (video_dir / "scenes").mkdir(parents=True)
    (ROOT / "videos" / "__init__.py").touch()
    (video_dir / "__init__.py").touch()
    (video_dir / "scenes" / "__init__.py").touch()

    (video_dir / "AGENTS.md").write_text(
        AGENTS_TEMPLATE.format(title=args.title, slug=args.slug)
    )
    (video_dir / "render.py").write_text(
        RENDER_TEMPLATE.format(title=args.title, slug=args.slug)
    )
    (video_dir / "scenes.json").write_text(
        json.dumps({"title": args.title, "slug": args.slug, "scenes": []}, indent=2) + "\n"
    )
    (video_dir / "feature_list.json").write_text(
        json.dumps(
            {"video": args.title, "slug": args.slug, "features": []}, indent=2
        )
        + "\n"
    )
    (video_dir / "claude-progress.txt").write_text(
        f"# Progress log — {args.title}\n\n"
        "Newest entry last. One entry per session: what you did, what you tried "
        "that did not work, and what the next session should pick up.\n\n"
        "--------------------------------------------------------------------\n"
        "SETUP — project scaffolded by scripts/new_video.py. No scenes yet.\n"
    )
    (video_dir / "script.md").write_text(
        f"# {args.title} — script\n\n"
        "One section per scene: narration, on-screen beats, duration budget.\n"
    )

    print(f"created videos/{args.slug}/")
    print("next: fill script.md, then add scenes to feature_list.json and scenes.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
