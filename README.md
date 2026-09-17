# manim-videos

A reusable harness for producing 3Blue1Brown-style technical explainer videos
with [Manim](https://www.manim.community/). Shared visual components live in
`lib/`; each video is a self-contained project under `videos/`. The point is
that video N+1 costs less than video N.

## Quick start

```bash
./init.sh                                          # environment, idempotent
.venv/bin/python scripts/evaluate.py               # verify the repo is healthy
.venv/bin/python videos/chatgpt_message_journey/render.py --profile draft
```

## What is here

- **`lib/`** — the visual vocabulary reused across every video: chat UI, tokens,
  vectors and embeddings, network transport, probability distributions, and
  transformer internals, all built on one theme.
- **`videos/`** — one folder per video, each with its own script, feature list,
  progress log, scenes and render driver.
- **`tests/`** — structural and visual-regression tests for `lib/`.
- **`scripts/evaluate.py`** — the gate. Nothing is done until it exits 0.

`AGENTS.md` is the entry point for anyone, human or agent, working in the repo.
`docs/` holds the depth: session playbook, component guide, architecture notes.

## First video

**"What happens when you send a message to ChatGPT"** — eight scenes tracing one
message from the composer through network transport, tokenization, embedding,
the transformer stack, sampling and streaming, and back onto the screen. Scenes
1 (User Input) and 3 (Tokenization) are built; the rest are planned with
acceptance criteria in `videos/chatgpt_message_journey/feature_list.json`.

## Adding a video

```bash
.venv/bin/python scripts/new_video.py my_video_slug --title "My video"
```

This scaffolds the per-video harness files. Fill in `script.md` first, then work
one scene per session against the feature list.
