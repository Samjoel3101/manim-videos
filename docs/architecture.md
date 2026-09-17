# Architecture

## Layering

```
videos/<slug>/scenes/   narrative: what happens, in what order, with what words
        │ imports
        ▼
lib/components/         vocabulary: what things look like
        │ imports
        ▼
lib/theme.py            identity: colour, type, spacing, timing
```

The dependency direction is one-way. `/lib` must never import from `/videos` — a
component that knows about a specific video is not a component, it is a scene
fragment in the wrong folder. Nothing enforces this mechanically yet; it is one
import-boundary lint rule away if it is ever violated, and that is the right
moment to add one.

## Why theme.py is a single module

Every value that makes the series look like one series lives in one file.
Changing `TOKEN` there recolours every token in every video at once. That is the
return on the harness: consistency by construction rather than by discipline.

## Why the repo is installed as an editable package

`manim render path/to/scene.py` puts the *scene's* directory on `sys.path`, not
the repo root. Installing the repo with `pip install -e .` lets every scene say
`from lib import ...` and keeps `sys.path` hacks out of the top of every file.

## Why video slugs are identifiers

The Evaluator imports scene modules by dotted path, so slugs are
`lowercase_with_underscores`, not hyphenated.

## Why scenes.json lists only built scenes

`feature_list.json` is the plan — all eight scenes, with acceptance criteria.
`scenes.json` is the render manifest of what actually exists. Keeping them
separate means `render.py` always cuts a watchable partial video, and the
Evaluator never tries to render a module nobody has written yet.

## Why snapshots are luminance signatures, not image diffs

A 16×16 grid of mean luminance is small enough to commit and to read in a diff,
stable across minor font-rasterisation differences, and sensitive to what
actually regresses: an element moving, disappearing, or changing size. Full image
diffs are more sensitive but flap across environments, and a flaky check teaches
everyone to ignore failures — which is worse than no check at all.

The cost is a real blind spot, stated plainly in `AGENTS.md`: small colour shifts
and single-glyph typos pass. Those need human eyes, and the harness says so
rather than letting silence imply "verified".

## Why the Evaluator is protected

An agent that can edit both its work and its grading can go green by weakening
the check. `scripts/evaluate.py`, the test fixtures and the approved baselines
are write-blocked for agent sessions; new test files are not, because the
generator is *required* to add tests.

The hook is a guard rail, not a security boundary — a process that does not go
through a tool call can still write anywhere. A CI job running the Evaluator from
the base branch is the real gate, and is the first thing to add once this repo
sees pull-request volume.

## What is deliberately not here yet

Following the harness-engineering skill's warning about over-scaffolding a fresh
repo: no CI pipeline, no agent-to-agent review, no import-boundary linting, no
multi-agent role split, no gardening cron. Each solves a problem this repo has
not had yet. Add them when a real failure asks for them, not before — and prune
anything here that stops earning its keep.
