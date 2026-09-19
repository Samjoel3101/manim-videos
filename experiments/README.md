# experiments/

Throwaway spikes. **Nothing in here is shipped, tested, or wired into the
Evaluator**, and nothing in `lib/`, `videos/`, `tests/` or `assets/` imports it.
Each spike answers one question and then either graduates into a real proposal
or gets deleted.

## slides_lifecycle — click-to-advance presentation (status: spike, undecided)

**Question:** is a click-driven deck good enough to present this material,
compared with the continuous uncut take the repo ships?

`slides_lifecycle/slides_scene.py` subclasses the shipped `TheLifecycle` scene
and calls its existing beat methods with `manim_slides.Slide.next_slide()`
between them. It copies **no** choreography — the timings in
`videos/chatgpt_request_lifecycle/` remain the single source of truth. The spike
covers the top band only (client → edge → gateway → orchestrator) and inserts
exactly one `next_slide(loop=True)`, so a frozen pause and an animated idle can
be compared side by side.

Build it:

```bash
.venv/bin/pip install "manim-slides>=5.7"
.venv/bin/python experiments/slides_lifecycle/build.py              # 480p15
.venv/bin/python experiments/slides_lifecycle/build.py --profile final
```

The output is a single self-contained HTML file under `out/_experiments/`
(`out/` is gitignored) that opens from disk with no server and no network.

Notes:

- `manim-slides` is a spike-only dependency. It is in `requirements.txt` so the
  build is reproducible, but no shipped code imports it.
- The render writes a slide config into `./slides/` at the repo root. That
  directory is gitignored; the chunk mp4s are not committed.
- The shipped films are untouched, `lib/` is untouched, and the Evaluator gates
  are unchanged.

### Reproducibility note: Reveal.js assets

`convert --offline` inlines Reveal.js, which it downloads from a CDN on first
use and then caches under `~/.cache/manim-slides/revealjs<version>/`. In a
sandbox whose egress policy blocks `cdn.jsdelivr.net`, `cdnjs.cloudflare.com`
and `unpkg.com`, the convert step fails with `Missing Reveal.js asset`. The
cache can be primed from any source that is reachable — the six files it wants
for Reveal 6.0.1 are `reveal.css`, `black.css`, `zenburn.css`, `reveal.js`,
`notes.js` and `markdown.js`, taken from `dist/` (and `dist/plugin/`) of the
`reveal.js` npm tarball. Once cached, the build is fully offline.
