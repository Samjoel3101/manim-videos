# Slides — the click-advanced deck of every film

Every video in this repo has two outputs from **one** choreography:

- the continuous uncut take (`videos/<slug>/render.py` → `assets/<slug>.mp4`);
- a click-advanced deck (`scripts/build_slides.py <slug>` → one self-contained
  HTML file) that a presenter steps through.

The deck is not a second edit. It **subclasses** the shipped scene and decides
only *where the clicks go*, so `videos/<slug>/script.md` stays the single source
of truth for every timing in both outputs. A deck that copies a `run_time` has
already failed.

This is a repo convention, not a suggestion: `tests/test_slides_convention.py`
runs inside the Evaluator's `unit` gate and fails a video that has no deck, a
deck that does not subclass its film, or a split that produces a stop nobody can
see.

Two halves below: **how the splitting works**, and **how to author a scene that
converts seamlessly**. The second is the one to read before writing a beat.

---

## 1. The files

| Path | What it is |
|---|---|
| `lib/slides.py` | `ClickDeck`, the generic split machinery. ~200 lines, shared. |
| `videos/<slug>/slides.py` | The per-video deck. What is specific to this film. |
| `scripts/build_slides.py` | Render + convert, and `--probe` for the inner loop. |
| `tests/test_slides_convention.py` | The enforcement, via the existing `unit` gate. |

A deck for a film with no ramps is about forty lines, most of them the import
preamble:

```python
class SlidesFoo(ClickDeck, Slide, TheFoo):
    EXPECTED_ANIMATIONS = 43
    EXPECTED_STOPS = 33
```

`ClickDeck.construct` calls `super().construct()` — the shipped `construct`,
unchanged — and then prints the split report, so a deck defines no `construct`
of its own. The test enforces that: a deck that re-implements the beat order is
a second copy of it.

**Base order matters.** `ClickDeck` first so its `play` override wraps
everything, `manim_slides.Slide` next so its `construct`-time bookkeeping wraps
the render, the film's scene last. The MRO is

```
SlidesFoo -> ClickDeck -> Slide -> BaseSlide -> TheFoo -> MovingCameraScene -> Scene
```

`lib/slides.py` deliberately does **not** import `manim_slides`; it is a plain
mixin over `Scene`. That keeps `lib/` importable without a presentation library
and keeps the Evaluator's `import` gate honest. The `Slide` base comes from the
per-video deck.

---

## 2. How the splitting works

Granularity is **one click per animation**. Stopping once per *beat* is a
slideshow of four long movies, not a deck. `ClickDeck.play` is overridden so
every animation the shipped choreography runs gets its own stop, with no beat
rewritten. Four behaviours are load-bearing, and each was paid for by looking at
a rendered frame.

### 2.1 Pure-`Wait` plays are filtered out

`Scene.wait()` is `self.play(Wait(...))` in manim 0.21
(`manim/scene/scene.py:1252`). A naive split on every `play` therefore turns
each per-character hold of `ChatInput.type_animation` into its own one-frame
slide — the first probe of this produced 57 stops, **29 of them a single frame**.

`ClickDeck._is_pure_wait` filters them: a pure-`Wait` play neither opens a slide
nor disturbs the merge flag. Two consequences worth stating plainly:

- typing runs *inside* whatever slide is open, so the deck's first stop rests on
  the fully typed question;
- **a narration hold costs no click.** It extends the slide that is already
  open. The lifecycle film gained fifteen bare `self.wait(t)` holds in one
  commit and the deck's stop count did not move — 97 animations, 70 stops before
  and after.

### 2.2 A stop rests on the END of its animation

`next_slide()` closes the open slide *before* the animation it precedes. That is
the whole point: the click lands on the filled checklist, the grown meter, the
completed legend — never on a fade in progress.

### 2.3 Clear-downs merge FORWARD

Every beat clears its own props before the camera leaves. That is already a
house rule, and it is *why* this merge is possible.

On its own, a clear-down makes a stop whose entire content is "the text you were
reading disappears", ending on an empty bay. So the split is taken *before* the
clear-down — it opens a new slide — and **suppressed before the play that
follows it**. One click then reads "old props clear, camera moves on, new
content appears", and rests on the new content. Thirteen plays merge forward
this way across the lifecycle film; their chunk durations are the sum of both
plays' `run_time`s, which is how the merge is checked.

**Direction is everything.** Suppressing before the clear-down instead merges it
into the *previous* slide, so content would appear and instantly vanish under a
single click. Same number of stops, opposite behaviour, and the counts cannot
tell you which you have.

Detecting a clear-down is not "contains a `FadeOut`", and not "every animation
is a `FadeOut`" either — real tails pair their fades with a glow dimming to its
resting stroke and a packet dropping to the next rail, so the strict test would
match none of them. The predicate (`ClickDeck._is_clear_down`) is **at least one
`FadeOut` and nothing being introduced**, where introduced means one of
`INTRODUCING` — `FadeIn`, `Flash`, `Create`, `DrawBorderThenFill`,
`MoveAlongPath`.

Two parts of that took a render and a frame to get right:

- *Introduced* is not the same as `FadeIn`. `beat_sample` absorbs the sampled
  chip into the cache with `Flash(kv) + FadeOut(kv)`
  (`videos/chatgpt_request_lifecycle/scenes/scene_lifecycle.py:945-950`); a
  FadeIn-only test reads that as a clear-down and merges it into the genuine
  clear-down after it, so the stop rests on a cleared bay.
- **A camera move does not disqualify a clear-down.** An earlier cut also
  required the camera to stay put, reasoning that "the props go while the camera
  carries on" is a transition. The frames do not support the distinction: such a
  play ends on the same half-faded prop, because Manim renders an animation's
  last frame at `t = run_time - 1/fps` and `FadeOut` only removes the mobject
  after that. `scene_lifecycle.py:957` proved it — the sampler's loop caption was
  clearly legible, mid-fade, on a resting frame.

### 2.4 Some repeats must not become clicks

`ClickDeck.no_stops()` is a context manager that suppresses splitting for a
region. Its **first** play still opens a stop, so a suppressed region is its own
click rather than an extension of the one before it.

Two variants exist for ramps written inline in a beat the deck may not edit,
where there is no call to wrap:

- `sticky_stops()` — wrap one *repetition*. The region opens at the first one
  and stays open; `play` closes it at the first animation that does not come
  from inside a repetition. `videos/chatgpt_request_lifecycle/slides.py` uses it
  for the six `CYCLES_FAST` decode cycles.
- `_sticky_play(args)` — recognise a repetition by *what it animates*. Override
  it on the deck. `videos/chatgpt_message_journey/slides.py` uses it for the
  four `LayerBlock` activate/deactivate pulses that climb the transformer stack.
  Recognise by mobject, never by index: an index moves silently when a beat is
  re-ordered.

**The rule for deciding: keep the stops unless the repetition is a ramp or a
texture rather than a sequence of distinct states.** Worked examples, both
directions:

| Repeat | Call | Why |
|---|---|---|
| lifecycle `CYCLES_FAST`, six cycles | **one click for the whole ramp** | The list halves across six passes and the film's own comment (`scene_lifecycle.py:174-186`) says its shape IS the acceleration. Six clicks flatten it as surely as re-timing it would. |
| lifecycle `CYCLES_EXPLICIT`, four cycles | one click each | The film says the viewer is meant to *count* these: one click, one token, one more word (`A` → `A dozen` → …). |
| lifecycle orchestrator context bar | **four fill stops kept** | `range(1, len(bar)+1)` over four segments; each stop rests on a different filled state, plus the `emphasise` stop after them. Five distinct bar states. |
| lifecycle decode-bay pulses | kept | The batch lanes advance a step on each one, so every stop differs from the one before it. |
| lifecycle `beat_stream` packets | kept | Already a single `LaggedStart`, i.e. one play. |
| journey transformer-stack pulses | **one click** | Every `deactivate` returns its block exactly where it started, so four of the eight clicks show the bay precisely as the click before it left it. |

### 2.5 Looping stops

`LOOP_ON_ANIMATION` gives one stop a looping (rather than frozen) hold. A loop
is honest only for an animation that **ends where it began** — a live idle such
as typing dots. A token lapping a loop or a packet flying home ends somewhere
else, so looping it teleports the dot on replay.

An index is only as good as the ordering behind it, so a deck that sets
`LOOP_ON_ANIMATION` should override `_is_loop_target` to check the animation
itself at the split site. The counts tripwire is a proxy: a reorder that
preserves the counts moves the loop silently.

---

## 3. Authoring rules — how to write a scene that converts seamlessly

Write these into the *film*. They cost the film nothing and they are what makes
the deck fall out for free.

1. **A bare `self.wait()` never creates a click — it extends the open slide.**
   So a narration hold is free in the deck. But a wait placed *after* a
   clear-down parks the stop on the cleared state: the disappearing-text bug.
   Fourteen of the lifecycle film's fifteen holds follow a content play, and the
   fifteenth is the last play of the film, where the trailing wait is what
   carries the stop past the final fade.

2. **Each beat clears its own props before the camera leaves.** Already a house
   rule; the deck depends on it, and it is why clear-downs can merge forward.

3. **Content must arrive via a recognised arrival class** — `FadeIn`, `Flash`,
   `Create`, `DrawBorderThenFill`, `MoveAlongPath`.

4. **`.animate` is never an arrival.** It is how glows, meters and the camera
   move, and that is right for all of them. It is wrong for a bare
   `.animate.set_opacity(1.0)`: a `_MethodAnimation` does not advertise its
   direction, so an opacity raise paired with a `FadeOut` and nothing else is
   **misclassified as a clear-down**. Bring content in with `FadeIn` instead.

   This is not hypothetical. `videos/chatgpt_message_journey/scenes/scene_factory.py:348-354`
   plays `camera.focus(...) + FadeOut(courier) + self.answer.body.animate.set_opacity(1.0)`.
   The reply bubble's body is genuinely *arriving* there, but the deck reads the
   play as a clear-down and merges it forward into the three-word reveal after
   it. That film is correct and is left alone; its deck carries the defect in a
   comment. A new beat should use `FadeIn(self.answer.body)`.

5. **Wrap ramps and textures in `no_stops()`** (or recognise them with
   `_sticky_play`). See the table in §2.4 for which way to call it.

6. **End a film with a trailing wait**, so the last stop rests past the final
   fade. The lifecycle film ends `self.play(FadeOut(caption))` then
   `self.wait(0.9)`; its last chunk is 1.133s for a 0.25s fade, and the final
   frame is the whole plant at rest with the finished reply in the bubble.

7. **Do not add a settling wait before a stop.** Commit `714204e` added a 0.2s
   `self.wait()` before each beat-level stop, which was the right fix at that
   granularity and is exactly wrong at this one — a trailing wait is a
   pure-`Wait` play, so it extends the slide *past* the animation and parks the
   stop on the cleared state. Merging clear-downs forward removes the need.

8. **Watch `Transform` if you extend `INTRODUCING`.** `.animate` resolves to
   `_MethodAnimation`, whose MRO runs `MoveToTarget -> Transform` and does *not*
   pass through `ApplyMethod`. Listing `Transform` silently classifies every
   built `.animate` — `camera.focus` included — as an arrival, which reinstates
   the "a camera move disqualifies a clear-down" rule §2.3 removes, **while
   leaving the stop count identical**. It was caught by looking at a frame, not
   at the numbers.

---

## 4. Building and checking a deck

```bash
.venv/bin/python scripts/build_slides.py <slug> --probe          # seconds, no render
.venv/bin/python scripts/build_slides.py <slug>                  # 480p15 + HTML
.venv/bin/python scripts/build_slides.py <slug> --profile final  # 1080p60
.venv/bin/python scripts/build_slides.py <slug> --skip-render    # re-convert only
```

`--probe` runs the deck's `construct` with the frame loop replaced by "advance
every animation to its final state" (`lib.slides.probe`). The whole split state
machine executes — the same `play` override, the same merges, the same
suppressed regions — in seconds rather than the minutes a render costs. It is
the inner loop, and it is the same code path the test uses.

The render emits two things from one pass: the per-slide chunks manim-slides
plays, and an ordinary continuous mp4, which is what you extract frames from to
review. `manim-slides convert --one-file --offline` then inlines every chunk and
the whole reveal.js runtime into a single self-contained page that opens from
disk with no server and no network.

Output goes to `out/<slug>/slides_<profile>/` and the slide config to
`slides/`. Both are gitignored; **chunk mp4s are never committed.**

### Reveal.js offline cache — not guessable, so it is written down

`convert --offline` inlines Reveal.js, which it downloads from a CDN on first
use and then caches under `~/.cache/manim-slides/revealjs<version>/`. In a
sandbox whose egress policy blocks `cdn.jsdelivr.net`, `cdnjs.cloudflare.com`
and `unpkg.com`, the convert step fails with `Missing Reveal.js asset`.

The cache can be primed from any reachable source. For Reveal 6.0.1 it wants six
files — `reveal.css`, `black.css`, `zenburn.css`, `reveal.js`, `notes.js` and
`markdown.js` — taken from `dist/` and `dist/plugin/` of the `reveal.js` npm
tarball. Once cached, the build is fully offline.

---

## 5. What the gate checks

`tests/test_slides_convention.py` runs under the existing `unit` gate — no gate
name was added to `harness.json`, and `scripts/evaluate.py` is untouched,
because `gate_unit` runs `pytest tests/` over the whole directory. For every
video under `videos/`:

- a `slides.py` exists and exposes exactly one `ClickDeck` subclass;
- that deck subclasses a scene named in the video's `scenes.json`, with
  `ClickDeck` ahead of it in the MRO;
- the deck defines no `construct` of its own;
- no stop is zero-length or a single frame at the Evaluator's render profile;
- the deck's total time equals the film's, so the split adds and loses no time;
- `EXPECTED_ANIMATIONS`/`EXPECTED_STOPS` still match.

It renders nothing, but it does build two whole films' worth of mobjects, so it
costs about 45s — roughly seven times the rest of the unit suite, and two orders
of magnitude less than proving the same thing with a render.

## 6. Current decks

| Video | Animations | Stops | Total |
|---|---|---|---|
| `chatgpt_request_lifecycle` | 97 | 70 | 59.399s rendered (59.516s nominal) |
| `chatgpt_message_journey` | 43 | 33 | 28.212s nominal |

Lifecycle chunk durations run 0.20s–2.67s, median 0.83s; none is a single frame
and the shortest is three frames at 15fps. The ramp chunk is 2.67s against 2.34s
of nominal `run_time` — frame rounding at 15fps, not a stretched animation.
