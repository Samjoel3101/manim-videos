# Manim video harness

A repo for producing 3Blue1Brown-style technical explainers continuously. The
point is that **video N+1 costs less than video N**, because the visual
vocabulary already exists in `/lib`.

## Map

| Path | What it is |
|---|---|
| `lib/theme.py` | Colour, type, spacing, timing. The series' visual identity. |
| `lib/components/` | Reusable visuals as VGroup subclasses. Check here first. |
| `lib/transitions.py`, `lib/utils.py` | Scene transitions; text/layout helpers. |
| `videos/<slug>/` | One self-contained video. Has its own AGENTS.md. |
| `tests/` | Structural + visual-regression tests for `/lib`. |
| `scripts/evaluate.py` | **The Evaluator.** Nothing is done until it exits 0. |
| `harness.json` | Run config: render profiles, gates, protected paths. |
| `init.sh` | Idempotent environment bootstrap. Run it every session. |
| `claude-progress.txt` | Repo-level session log. Read it before starting. |
| `feature_list.json` | Repo-level (harness/lib) work items and their status. |
| `docs/` | Depth, loaded on demand — see below. |

Deeper reading, only when you need it: `docs/session-playbook.md` (how a session
runs), `docs/component-guide.md` (how to write a `/lib` component),
`docs/architecture.md` (why the layering is what it is).

## Roles

**Generator** — builds scenes and components. **Evaluator** — `scripts/evaluate.py`,
which the generator runs but may not edit. The split exists because an agent that
can change both the work and its grading can pass by weakening the check.

### Rules for the Generator

1. **Check `/lib/components/` before writing any new visual.** Extend or
   parametrize what is there rather than duplicating it. A new `ChatBubble`
   variant is a keyword argument, not a second class.
2. **Only promote into `/lib` when it is genuinely reusable** — used by 2+ scenes,
   or clearly needed by a future video. One-offs stay in the video's `scenes/`.
   When a second scene needs a local helper, that is the moment to promote it.
3. **Every new `/lib` component needs a matching test in `/tests/` before it is
   done.** Structural test always; a snapshot case if it has meaningful layout.
4. Pull colour, size, spacing and timing from `lib/theme.py`. A hex string or a
   raw `run_time=0.7` in a scene is a bug — it breaks series consistency.
5. Leave the repo merge-ready at the end of a session: green Evaluator, updated
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
.venv/bin/python scripts/new_video.py <slug> --title "..."  # scaffold a video
```

Slugs are lowercase with underscores — the Evaluator imports scene modules by
dotted path.
