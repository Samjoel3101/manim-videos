# experiments/

Throwaway spikes. **Nothing in here is shipped, tested, or wired into the
Evaluator**, and nothing in `lib/`, `videos/`, `tests/` or `assets/` imports it.
Each spike answers one question and then either graduates into a real proposal
or gets deleted.

## slides_lifecycle — click-to-advance presentation (status: spike, undecided)

**Question:** is a click-driven deck good enough to present this material,
compared with the continuous uncut take the repo ships?

`slides_lifecycle/slides_scene.py` subclasses the shipped `TheLifecycle` scene
and runs its existing beat methods unchanged. It copies **no** choreography —
the timings in `videos/chatgpt_request_lifecycle/` remain the single source of
truth. The spike covers the top band only (client → edge → gateway →
orchestrator).

### Granularity: one click per animation

The first cut stopped once per *beat*: four stops, i.e. a slideshow of four long
movies. This one overrides `Scene.play` instead, so **every animation the
shipped choreography runs gets its own stop** — 28 animations, 27 stops,
0.20s–1.93s each (median 0.60s), none of them a single frame. Three things make
that work:

- **`Scene.wait()` is `self.play(Wait(...))`** in manim 0.21. Splitting on every
  `play` therefore turns each per-character hold of `ChatInput.type_animation`
  into its own one-frame slide — the first probe of this produced 57 stops, 29
  of them one frame long. Pure-`Wait` plays are filtered out, so the typing runs
  *inside* the open slide and the deck's first stop rests on the fully typed
  question.
- **A stop rests on the END of its animation**, because `next_slide()` closes
  the slide *before* the animation it precedes. The click lands on the filled
  checklist, the grown meter, the completed legend.
- **Clear-downs merge forward.** Every shipped beat clears its own props before
  the camera leaves. Left alone, such a play makes a stop whose whole content is
  "the text you were reading disappears", ending on an empty bay. So the split
  is taken *before* the clear-down and **suppressed before the play that follows
  it**, giving one click that reads "old props clear, camera moves on, new
  content appears". The direction matters and is easy to get backwards:
  suppressing before the clear-down instead merges it into the *previous* slide,
  so content would appear and instantly vanish under a single click. Two stops
  are merged this way (edge→gateway, gateway→orchestrator); their chunk
  durations are the sum of both plays' `run_time`s, which is how the merge is
  checked.

Detecting a clear-down is not "contains a `FadeOut`" — the beats also combine a
`FadeOut` with a `camera.focus` move in one `play`, and that is a transition,
not a clear-down. Nor is it "every animation is a `FadeOut`": the real tails
pair their fades with a glow dimming to its resting stroke, and with the packet
dropping to the next rail. The predicate is: at least one `FadeOut`, nothing
being introduced, and the camera staying put.

The one animated hold is on **animation 3, the typing-indicator dots** — the
only animation in the top band whose replay reads as a live idle rather than a
value snapping back to its start. Every other stop freezes, so the two can be
compared in one sitting. That contrast is what this spike asks a viewer to
judge.

### Why the `SETTLE` wait went

Commit `714204e` put a 0.2s `self.wait()` before each beat-level stop, because
manim renders an animation's final frame at `t = run_time - 1/fps` and a beat's
last play is a `FadeOut`, so the chunk was cut while the fading props were still
faintly drawn. At this granularity that fix is exactly wrong: a trailing wait is
a pure-`Wait` play, so it extends the slide *past* the animation and parks the
stop on the cleared state — the disappearing-text problem, reintroduced.
Merging clear-downs forward removes the need for it.

One hold survives, `END_HOLD`, at the very end of the deck only: the last
clear-down has no successor to merge into and no next slide to carry the frame.
Without it the final still is a half-faded caption (confirmed by extracting it);
with it the deck ends on the emptied band with the packet on the rail down into
the inference stack.

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
