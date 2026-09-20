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
truth. The spike covers the **whole film**: all eleven beats, client through
pull-back, including the two values the shipped `construct` threads between
beats (the token strip into `beat_prefill`, the winning chip into
`beat_stream`). An earlier round covered the top band only; nothing about that
round's per-transition behaviour changed when the other seven beats were
added.

### Granularity: one click per animation

The first cut stopped once per *beat*: four stops, i.e. a slideshow of four long
movies. This one overrides `Scene.play` instead, so **every animation the
shipped choreography runs gets its own stop** — 97 animations, 70 stops,
0.20s–2.67s each (median 0.83s), none of them a single frame and none under
0.2s. Four things make that work:

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
  so content would appear and instantly vanish under a single click. Thirteen
  plays merge forward this way across the film; their chunk durations are the
  sum of both plays' `run_time`s, which is how the merge is checked.
- **Repeats whose shape is the content play through under one click** — see
  "The loops that must not become clicks" below.

Detecting a clear-down is not "contains a `FadeOut`": the real tails pair their
fades with a glow dimming to its resting stroke, and with the packet dropping to
the next rail, so "every animation is a `FadeOut`" would match none of them. The
predicate is **at least one `FadeOut` and nothing being introduced**, and two
parts of that took a render and a frame to get right:

- *Introduced* is not the same as `FadeIn`. `beat_sample` absorbs the sampled
  chip into the cache with `Flash(kv) + FadeOut(kv)`; a FadeIn-only test reads
  that as a clear-down and merges it into the genuine clear-down after it, so
  the stop rests on a cleared bay. Arrival is now a list of classes — `FadeIn`,
  `Flash`, `Create`, `DrawBorderThenFill`, `MoveAlongPath`. A `.animate` call is
  deliberately never an arrival (it is how the glows, the meters and the camera
  are animated); a bare `.animate.set_opacity(1.0)` paired with a `FadeOut` and
  nothing else would therefore be misclassified. No play in this film is one.
- **A camera move no longer disqualifies a clear-down.** The top-band cut also
  required the camera to stay put, reasoning that "the props go while the camera
  carries on" is a transition rather than a clear-down. The frames do not
  support the distinction: such a play ends on the same half-faded prop, because
  Manim renders an animation's last frame at `t = run_time - 1/fps` and
  `FadeOut` only removes the mobject after that. `scene_lifecycle.py:957` proved
  it — the sampler's loop caption was clearly legible, mid-fade, on a resting
  frame. Two plays change as a result (`:957`, and `:1071` where the spinner goes
  as the camera returns to the chat, which used to rest on an *empty* bubble
  frame); no play in the top band combines a `FadeOut` with a camera move, so
  the 27 stops already signed off on are unchanged, which was checked by diffing
  every chunk duration against the previous render.

Watch out for `Transform` if you extend the arrival list: `.animate` resolves to
`_MethodAnimation`, whose MRO runs `MoveToTarget -> Transform` and does *not*
pass through `ApplyMethod`. Listing `Transform` silently classifies every built
`.animate` — including `camera.focus` — as an arrival, which reinstates the
camera rule above while leaving the stop count identical. It was caught by
looking at the frame, not at the numbers.

### The loops that must not become clicks

The back half repeats structures the top band does not, and `no_stops()` — a
context manager that suppresses splitting for a region — decides which of them
step and which play through. Its first play still opens a stop, so a suppressed
region is its own click rather than an extension of the one before it.

**Suppressed: the token cycles in `beat_pull_back`.** Each cycle is two plays
(lap the loop, then fly a token home and reveal a word), and split per play the
first of the two rests on a dot back where it started with no new word — a click
that shows nothing. So every cycle is one click. On top of that, the six
`CYCLES_FAST` cycles are **one click for the whole ramp**: that list halves
across six passes and the film's own comment (`scene_lifecycle.py:174-186`) says
its shape IS the acceleration. Six clicks flatten it as surely as re-timing it
would, twelve worse. The four `CYCLES_EXPLICIT` cycles keep a click each,
because they are the ones the film says the viewer is meant to *count*: one
click, one token, one more word, which the frames show (`A` → `A dozen` → … →
`A dozen machines touch it`), and then the ramp's single click lands the
remaining six words at once. The ramp chunk is 2.67s against 2.34s of nominal
`run_time` — frame rounding at 15fps, not a stretched animation.

Because the cycle loop sits in the middle of a beat this scene may not edit,
the ramp's region is opened by the first fast cycle and closed by `play` at the
first animation that does not come from inside a cycle. That is the only sticky
region in the file.

**Not suppressed, deliberately:** the orchestrator's context bar (`:519`), which
fills one segment per click — **four** fill stops (deck stops 21–24), one per
segment of a four-segment bar, plus the `emphasise` stop after them, i.e. the
five distinct bar states the user singled out as good. An earlier draft of this
file called the fill loop itself "five stops"; the loop is `range(1, len(bar)+1)`
over four segments and always produced four. The frames were re-checked after
the bar was rebuilt (`length` 2.3 → 4.9, legend moved below it): each stop still
rests on a filled state, and the legend's four names are now legible at 480p15,
which they were not in the beside-the-bar layout. The decode bay's three
activate/deactivate pulses
(`:777`), because the batch lanes advance a step on each one, so every stop
differs from the one before it and all six rest on a full bay; and
`beat_stream`'s four packets, which are a single `LaggedStart`, i.e. already one
play. The rule applied throughout: keep the stops unless the repetition is a
ramp or a texture rather than a sequence of distinct states.

### The one animated hold

It is on **animation 3, the typing-indicator dots** — still the only animation
in the film whose replay reads as a live idle rather than a value snapping back
to its start (the back half's candidates, a token lapping the loop or flying
home, end somewhere other than where they began, so looping them teleports the
dot). Every other stop freezes, so the two can be compared in one sitting. That
contrast is what this spike asks a viewer to judge. The index is checked against
the animation itself at the split site now, not just against the totals: a
reorder that preserved the counts would otherwise move the loop silently.

### Why the `SETTLE` wait went

Commit `714204e` put a 0.2s `self.wait()` before each beat-level stop, because
manim renders an animation's final frame at `t = run_time - 1/fps` and a beat's
last play is a `FadeOut`, so the chunk was cut while the fading props were still
faintly drawn. At this granularity that fix is exactly wrong: a trailing wait is
a pure-`Wait` play, so it extends the slide *past* the animation and parks the
stop on the cleared state — the disappearing-text problem, reintroduced.
Merging clear-downs forward removes the need for it.

**`END_HOLD` is gone.** The top-band cut kept one hold at the very end, because
that cut stopped after `beat_orchestrator`, whose last play is a clear-down with
no successor to merge into and no next slide to carry the frame. The full film
does not need it: `beat_pull_back` ends with `self.play(FadeOut(caption))`
followed by the shipped `self.wait(0.9)`, and a trailing wait is a pure-`Wait`
play, so it already extends the final slide past the fade. The deck's last chunk
is 1.133s for a 0.25s fade, and its final frame is the whole plant at rest with
the finished reply in the bubble — checked by extracting it, not assumed. The
constant was removed rather than kept with a comment that is no longer true.

### The narration holds, and why they cost no stops

The film gained fifteen bare `self.wait(t)` narration holds (commit `c5405eb`),
plus `REQUEST_LAP_RUN_TIME` 1.6 → 2.2 and `CYCLES_EXPLICIT`'s lap 0.38 → 0.56.
The deck picked all of that up by inheriting, without a line of choreography
being copied — which is the property this spike is built on, and the reason the
merge was a merge rather than a rewrite.

**The stop count did not move: still 97 animations and 70 stops.** A hold is a
pure-`Wait` play, and those are filtered out of splitting, so a hold never makes
a click — it **extends the slide that is already open**. The distribution is
what changed: 0.20s–2.67s, median 0.83s (was 0.67s), 61.6s of chunk video for a
59.4s film. Histogram, in half-second bins: 22 stops under 0.5s, 19 in
0.5–1.0s, 20 in 1.0–1.5s, 6 in 1.5–2.0s, 2 in 2.0–2.5s, 1 at 2.67s. No stop is
a single frame; the shortest is 0.20s, i.e. three frames at 15fps.

The only way a hold can hurt is the `SETTLE` failure above: a hold placed
*after* a clear-down parks the stop on the emptied bay. All fifteen were
mapped to their slide and their preceding play, and **fourteen follow a content
play** — the frame the hold rests on is the frame the narration line is about,
which is exactly what a deck wants:

| hold | extends | rests on |
|---|---|---|
| `beat_client` 0.25 | stop 5 | the assembled `POST /v1/chat` card |
| `beat_edge` 0.35 | stop 12 | all three edge ticks struck |
| `beat_gateway` 0.35 | stop 17 | the quota meter settled at 62% |
| `beat_orchestrator` 1.0 | stop 25 | the built bar, sliver emphasised, caption up |
| `beat_orchestrator` 0.55 | stop 26 | both routing badges landed |
| `beat_tokenize` 0.4 | stop 29 | the token strip (slide opened by a clear-down that merged forward into it) |
| `beat_prefill` 0.75 | stop 33 | the cache bar with the tail emphasised |
| `beat_prefill` 0.5 | stop 34 | the second caption (merged-forward slide) |
| `beat_decode` 0.65 | stop 43 | the batch meter at 83% |
| `beat_sample` 0.45 | stop 48 | the winning `A` chip, after the `Flash` |
| `beat_sample` 1.0 | stop 51 | the `A` chip and the two-line loop caption |
| `beat_stream` 0.5 | stop 57 | the first word in the bubble (merged-forward slide) |
| `beat_after` 0.3 | stop 60 | all three after-the-response checks |
| `beat_pull_back` 0.5 | stop 61 | the whole plant, labelled and still |
| `beat_pull_back` 0.9 | stop 70 | the plant at rest with the finished reply |

Two of them were checked by hand because the mechanism makes them easy to
misread:

- **`beat_sample`'s 1.0s loop hold** sits after `Flash(kv) + FadeOut(kv)` — the
  copy being absorbed into the cache. That play contains a `FadeOut`, but
  `Flash` is an arrival, so it is not a clear-down, and the frame under the hold
  still carries the winning chip and both lines of the loop caption. Under a
  FadeIn-only arrival test it *would* have been a clear-down, and this hold
  would then have rested on a bay with nothing in it.
- **`beat_pull_back`'s final 0.9s hold** is the one hold that does follow a
  clear-down, and it is the case `END_HOLD` was deleted for: it is the last play
  of the film, so there is no successor to merge into, and the trailing wait is
  what carries the stop past the caption's fade. 0.5 → 0.9 makes that margin
  larger, not smaller. The extracted frame is the whole plant at rest with
  "A dozen machines touch it before the first word comes back." in the bubble
  and no ghost of the caption.

`REQUEST_LAP_RUN_TIME` and `CYCLES_EXPLICIT` only lengthen chunks the deck
already had: the lap is stop 62 at 2.2s, and the four explicit cycles are stops
64–67 at 1.0s each — still one click per countable token. `CYCLES_FAST` is
untouched, so the sticky region still takes the whole ramp under **one** click
(stop 69, 2.67s), and stop 70 is the final frame.

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
