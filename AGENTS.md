# Manim video harness

A repo for producing 3Blue1Brown-style technical explainers continuously. The
point is that **video N+1 costs less than video N**, because the visual
vocabulary already exists in `/lib`.

## Map

| Path | What it is |
|---|---|
| `lib/theme.py` | Colour, type, spacing, timing. The series' visual identity. |
| `lib/components/` | Reusable visuals as VGroup subclasses. Check here first. |
| `lib/camera.py` | Camera choreography for continuous, uncut shots. |
| `lib/motion.py` | **The motion language.** Easing curves and durations. |
| `lib/typography.py` | **The type system.** Sizes as a share of frame height. |
| `lib/routing.py` | Orthogonal rails, path joining, clearance assertions. |
| `lib/effects.py` | Glow, comet trails, pulses. |
| `lib/slides.py` | **`ClickDeck`.** Splits a film into a click-advanced deck. |
| `lib/assets/icons/` | Vendored Lucide icons (ISC). |
| `lib/transitions.py`, `lib/utils.py` | Scene transitions; text/layout helpers. |
| `videos/<slug>/` | One self-contained video. Has its own AGENTS.md. |
| `videos/<slug>/slides.py` | That video's deck. Subclasses the scene; copies no timings. |
| `tests/` | Structural + visual-regression tests for `/lib`. |
| `assets/` | The accepted cut of each video, committed. `out/` is scratch. |
| `scripts/build_slides.py` | Render a video's deck; `--probe` reports the split. |
| `scripts/evaluate.py` | **The Evaluator.** Nothing is done until it exits 0. |
| `harness.json` | Run config: render profiles, gates, protected paths. |
| `init.sh` | Idempotent environment bootstrap. Run it every session. |
| `claude-progress.txt` | Repo-level session log. Read it before starting. |
| `feature_list.json` | Repo-level (harness/lib) work items and their status. |
| `docs/` | Depth, loaded on demand — see below. |

Deeper reading, only when you need it: `docs/session-playbook.md` (how a session
runs), `docs/component-guide.md` (how to write a `/lib` component),
`docs/architecture.md` (why the layering is what it is), `docs/slides.md` (how a
film becomes a click deck, and how to author a beat so it converts).

## Roles

**Planner** — reads the request and the code, decides what to build, and writes
the plan. **Generator** — builds scenes and components from that plan.
**Reviewer** — checks the built result against the plan and against reality.
**Evaluator** — `scripts/evaluate.py`, which the generator runs but may not edit.

The Generator/Evaluator split exists because an agent that can change both the
work and its grading can pass by weakening the check. The Planner/Generator and
Generator/Reviewer splits exist for the same reason one step out: an agent that
decides what to build, builds it, and then judges its own build has no
independent check on any of the three. Every real defect this repo has shipped
was invisible to the gates and caught by a fresh pair of eyes.

## How a change is made — mandatory

**Plan → size it → build → review → verify.** Applies to *every* change to this
repo. Answering a question or read-only investigation is not a change.

1. **Plan first, in detail**, from the code rather than from memory. Write it to
   a file. **This step is never skipped, whatever the change is worth.**
2. **Size the change while planning**, and record the call in the plan:
   - **Small** — one or two files, no new module or public API, no new test or
     baseline, verified by a gate run rather than by reading frames, and
     statable in a few sentences → **build it yourself.**
   - **Large** — spans several files or modules, adds a feature, scene, beat or
     `/lib` component, needs new tests or a baseline, needs a render and a frame
     review to prove, or has parts that have to land in order → **hand the plan
     to a subagent to implement.**
   - On the boundary, **delegate**. Delegating a small change costs time;
     building a large one yourself removes the independent check that this
     whole section exists to provide.
3. **Review.** Delegated work always gets a separate reviewing subagent — one
   that did not write it. Self-built work gets one too if it touches `/lib` or
   anything already shipped in `assets/`.
4. **Verify the headline claims yourself.** A subagent's report is a claim, not
   a fact. This holds for your own work as well: run the Evaluator, look at the
   frames.

Full protocol — what a plan must contain, how to size it, how to brief each
subagent: `docs/session-playbook.md` → "Plan, delegate, review".

Nothing here licenses skipping the Evaluator, editing a protected path, or
approving a baseline without looking at the render.

### Rules for the Generator

1. **Check `/lib/components/` before writing any new visual.** Extend or
   parametrize what is there rather than duplicating it. A new `ChatBubble`
   variant is a keyword argument, not a second class.
2. **Only promote into `/lib` when it is genuinely reusable** — used by 2+ scenes,
   or clearly needed by a future video. One-offs stay in the video's `scenes/`.
   When a second scene needs a local helper, that is the moment to promote it.
3. **Every new `/lib` component needs a matching test in `/tests/` before it is
   done.** Structural test always; a snapshot case if it has meaningful layout.
4. Pull colour and spacing from `lib/theme.py`, **easing from `lib/motion.py`**
   and **type from `lib/typography.py`**. A hex string is a bug; so is a
   `self.play` without `rate_func=motion.*`; so is a raw `font_size=`. Type is
   sized against the shot it is read in, never in absolute points.
5. **Travel paths are built from the drawn rails** (`routing.join`), never from
   node centres, and a set asserts its own geometry in `validate()`.
6. **Nodes get icons, not labelled rectangles**, and "this is running" is a glow
   (`lib/effects.py`), not a thicker border.
7. **Every video ships two outputs from one choreography: the continuous film
   and a click-advanced deck** (`videos/<slug>/slides.py`). The deck subclasses
   the scene and decides only where the clicks go — it never copies a timing.
   Author beats for both: a bare `self.wait()` extends a slide rather than
   costing a click, each beat clears its own props, content arrives via `FadeIn`
   / `Flash` / `Create` / `MoveAlongPath` and **never** a bare
   `.animate.set_opacity(1.0)` paired with a `FadeOut`, and a ramp or texture
   goes in `no_stops()`. Full rules and the reason behind each:
   `docs/slides.md`. `tests/test_slides_convention.py` enforces this inside the
   existing `unit` gate.
8. Leave the repo merge-ready at the end of a session: green Evaluator, updated
   `feature_list.json` status, an appended `claude-progress.txt` entry.

## Session start

```bash
./init.sh                                   # environment, idempotent
cat claude-progress.txt | tail -40           # what the last session left
.venv/bin/python scripts/evaluate.py         # verify the claimed state holds
```

Then pick the highest-priority incomplete item from the relevant
`feature_list.json` — not the easiest one. Details in `docs/session-playbook.md`.

## The Evaluator

```bash
.venv/bin/python scripts/evaluate.py                          # lib gates
.venv/bin/python scripts/evaluate.py --video <slug>           # + render scenes
.venv/bin/python scripts/evaluate.py --video <slug> --scene X # one scene
.venv/bin/python scripts/evaluate.py --skip render            # fast inner loop
```

Gates: `lint` → `import` → `unit` → `snapshot` → `render`. A scene is done when
this is green, not when it "looks right" in isolation.

**Known blind spot:** snapshot tests compare a 16×16 luminance grid. They catch
layout, shape and contrast regressions. They do **not** catch small colour shifts
or single-glyph typos. Those need human spot-checking — do not report them as
verified.

## Protected paths

`scripts/evaluate.py`, `scripts/approve_baselines.py`, `tests/conftest.py`,
`tests/baselines/`, `.claude/hooks/`, `.github/workflows/`. Listed in
`harness.json` and enforced by a PreToolUse hook.

You **can** add new test files under `tests/` — rule 3 requires it. You cannot
edit the Evaluator, the fixtures, or the approved baselines. Re-approving a
baseline asserts "I looked at the render and it is correct":

```bash
.venv/bin/python scripts/approve_baselines.py            # show drift
.venv/bin/python scripts/approve_baselines.py <case>     # approve, after looking
```

If a check is genuinely wrong, note it in `claude-progress.txt` and raise it with
a human. Do not route around it.

## Rendering

```bash
.venv/bin/python videos/<slug>/render.py --profile draft    # 480p15, fast
.venv/bin/python videos/<slug>/render.py --profile final    # 1080p60
.venv/bin/python scripts/build_slides.py <slug> --probe     # deck split, no render
.venv/bin/python scripts/build_slides.py <slug>             # deck: chunks + one HTML
.venv/bin/python scripts/new_video.py <slug> --title "..."  # scaffold a video
```

Slugs are lowercase with underscores — the Evaluator imports scene modules by
dotted path.

## Continuous shots

The house format is one uncut camera move through a set that is built once, not
a sequence of scenes that cut between each other.

**Use the `factory-video` skill** (`.claude/skills/factory-video/`) when building
or changing one — it carries the full recipe. The essentials:

- Build the set in its own module (`scenes/<name>_set.py`) and the choreography
  in the scene. *Where things are* and *when the camera goes there* are separate
  concerns; mixing them gives you a scene nobody can re-time.
- Compose the set from `lib.components.factory` (`Station`, `PipelineBox`,
  `Conveyor`) and move the camera with `lib.camera`.
- Play camera moves *with* the action at their destination, not before it. That
  is why `camera.focus` returns an animation rather than playing one.
- A tight shot must clear its subject at 16:9. Frame height is width / 1.78, and
  a shot that crops the bottom of a bay is the commonest bug in this format —
  the tests cannot see it, so look at the frames.
- Motion blur is **off on every profile** by design — a frame-blend pass smears
  the whole frame and reads as judder on a camera move. The machinery stays for
  a shot that specifically wants it.
- The same choreography is also the deck (`docs/slides.md`). Nothing about the
  continuous shot changes for it — but a beat that clears its own props, brings
  content in with `FadeIn` rather than `.animate.set_opacity`, and keeps its
  narration holds after content rather than after a clear-down, converts for
  free. One that does not costs a click or a blank slide.
- Watch the zoom budget: the pull-back factor is `wide_frame_width / 14.22`. A
  wide layout reaches ~2x, a vertical column ~3x. Type is shot-relative so both
  stay readable, but a set should assert its own figure.
