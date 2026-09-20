#!/usr/bin/env python
"""Render a video's deck and convert it to ONE portable HTML file.

    .venv/bin/python scripts/build_slides.py <slug>                 # 480p15
    .venv/bin/python scripts/build_slides.py <slug> --profile final
    .venv/bin/python scripts/build_slides.py <slug> --probe         # no render

The render emits two things from a single pass: the per-slide chunks
manim-slides plays, and an ordinary continuous mp4 (which is what you extract
frames from to review). `manim-slides convert --one-file --offline` then inlines
every chunk and the whole reveal.js runtime into a single self-contained page,
so the deck opens from disk with no server and no network.

`--probe` runs the deck's `construct` with no rendering and prints the split it
produces — animations, stops, and the shortest and longest chunk. That is the
inner loop; it takes seconds where a render takes minutes. It is the same code
path `tests/test_slides_convention.py` uses.

**Reveal.js assets.** `convert --offline` inlines reveal.js, which it downloads
from a CDN on first use and caches under
`~/.cache/manim-slides/revealjs<version>/`. Behind an egress policy that blocks
`cdn.jsdelivr.net`, `cdnjs.cloudflare.com` and `unpkg.com`, the convert step
fails with `Missing Reveal.js asset`. Prime the cache from any reachable source:
for Reveal 6.0.1 it wants six files — `reveal.css`, `black.css`, `zenburn.css`,
`reveal.js`, `notes.js` and `markdown.js` — taken from `dist/` and
`dist/plugin/` of the `reveal.js` npm tarball. Once cached, the build is fully
offline.

See `docs/slides.md` for what a deck is and how to author a scene for one.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
with open(ROOT / "harness.json") as fh:
    HARNESS = json.load(fh)

PYTHON = str(ROOT / HARNESS["python"])
PROFILES = {
    name: spec
    for name, spec in HARNESS["render_profiles"].items()
    if name in ("draft", "preview", "final")
}


def run(cmd: list[str]) -> None:
    print("  $ " + " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"command failed ({result.returncode}): {' '.join(cmd)}")


def load_deck(slug: str):
    """Import `videos/<slug>/slides.py` and return (module_path, deck class)."""
    path = ROOT / "videos" / slug / "slides.py"
    if not path.exists():
        raise SystemExit(
            f"videos/{slug}/ has no slides.py — every video ships a deck. "
            "See docs/slides.md."
        )
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(f"_deck_{slug}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    from lib.slides import ClickDeck

    decks = [
        obj
        for obj in vars(module).values()
        if isinstance(obj, type)
        and issubclass(obj, ClickDeck)
        and obj is not ClickDeck
        and obj.__module__ == module.__name__
    ]
    if len(decks) != 1:
        raise SystemExit(
            f"videos/{slug}/slides.py must define exactly one deck, "
            f"found {[d.__name__ for d in decks]}"
        )
    return path, decks[0]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug")
    ap.add_argument("--profile", choices=sorted(PROFILES), default="draft")
    ap.add_argument("--probe", action="store_true",
                    help="report the split without rendering anything")
    ap.add_argument("--skip-render", action="store_true",
                    help="convert whatever slide config is already on disk")
    args = ap.parse_args(argv)

    path, deck = load_deck(args.slug)
    scene = deck.__name__

    if args.probe:
        from lib.slides import probe

        stats = probe(deck)
        chunks = stats.chunk_times
        ordered = sorted(chunks)
        print(
            f"\n{args.slug}: {stats.animations} animations -> {stats.stops} stops"
            f" ({stats.regions} suppressed regions)\n"
            f"  total    {stats.total_time:.6f}s\n"
            f"  shortest {ordered[0]:.2f}s   median {ordered[len(ordered) // 2]:.2f}s"
            f"   longest {ordered[-1]:.2f}s"
        )
        return 0

    profile = PROFILES[args.profile]
    media = ROOT / HARNESS["paths"]["output"] / args.slug / f"slides_{args.profile}"
    dest = media / f"{args.slug}_deck_{args.profile}.html"
    media.mkdir(parents=True, exist_ok=True)

    if not args.skip_render:
        run([PYTHON, "-m", "manim", "render", profile["flag"], "--disable_caching",
             "--media_dir", str(media), str(path), scene])

    # manim-slides writes its slide config to ./slides/ relative to the CWD.
    config = ROOT / "slides" / f"{scene}.json"
    if not config.exists():
        raise SystemExit(f"no slide config at {config} — did the render run?")

    run([PYTHON, "-m", "manim_slides", "convert", scene, str(dest),
         "--one-file", "--offline"])

    continuous = media / "videos" / path.stem / profile["dir"] / f"{scene}.mp4"
    print(f"\ndeck:       {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")
    print(f"config:     {config}")
    if continuous.exists():
        print(f"continuous: {continuous}")
    else:
        print("continuous: (not found — built with --skip-render?)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
