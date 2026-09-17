# What happens when you send a message to ChatGPT

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
4. `.venv/bin/python scripts/evaluate.py --video chatgpt_message_journey --scene <SceneClass>`
5. Only when that is green, flip the scene's status in `feature_list.json` and
   append to `claude-progress.txt`.

## Visual conventions for this video

_(fill in: recurring colours, camera framing, any motif this video repeats)_
