# What happens when you hit send

Video project. Read the root `AGENTS.md` first — it governs /lib and the
promotion rule. This file covers only what is specific to this video.

## Where things are

- `script.md` — narration and beat timings. The source of truth for pacing.
- `feature_list.json` — one entry per shot section. Status flags live here, not in prose.
- `claude-progress.txt` — what the last session did, tried, and left broken.
- `scenes.json` — the render manifest: scene order, module, duration budget.
- `scenes/lifecycle_set.py` — **the set**: where everything is.
- `scenes/scene_lifecycle.py` — **the choreography**: when the camera goes there.
- `scenes/props.py` — one-off visuals only this video needs.
- `render.py` — renders the scene and writes the cut.
- `slides.py` — the click deck of this film: 97 animations → 70 stops.
  Subclasses `TheLifecycle`; copies no timings. `docs/slides.md` has the rules.
  Build: `.venv/bin/python scripts/build_slides.py chatgpt_request_lifecycle`.

## Working on this video

1. `./init.sh` from the repo root.
2. Read `claude-progress.txt`, then `feature_list.json`; take the highest-priority
   `failing` item, not the easiest one.
3. Build the scene. Reuse `/lib` components; promote a local one only under the
   root AGENTS.md rule.
4. `.venv/bin/python scripts/evaluate.py --video chatgpt_request_lifecycle --scene TheLifecycle`
5. **Then look at the frames.** A zero exit code is not a review — see
   "Reviewing a change" below.
6. Only when that is green and the frames are right, flip the status in
   `feature_list.json` and append to `claude-progress.txt`.

## Visual conventions for this video

### The four bands

The set is a clockwise circuit around a 16:9-shaped world, read like a diagram:
left to right along the top, down the right-hand side, right to left along the
bottom, and up the left margin to close the loop.

| Band | y | What lives there |
|---|---|---|
| Top — the web tier | `BAND_TOP_Y = +9` | chat, bot check, edge, gateway, orchestrator |
| Right — the machine | column at `COLUMN_X = +18` | tokenizer, prefill, decode, sampler, inside one `PipelineBox` |
| Bottom — the reply | `BAND_BOT_Y = −12` | stream back, and the long climb home at `RETURN_X = −30.5` |
| Below — the epilogue | y = −16 | the after-response bay, on a faint spur |

Coordinates are **bay centres** and all of them live in `lifecycle_set.py`. They
are not repeated anywhere else, and `validate()` re-derives the box edges from
`llm.frame` rather than trusting a written-down number.

### Accents

| Station | Accent | Why |
|---|---|---|
| bot check | `WARN` | a gate, not a machine |
| Edge | `NETWORK` | transport |
| Gateway | `WARN` | policy and money |
| Orchestrator | `ASSISTANT` | the first server-side thing that is *ours* |
| Tokenizer | `TOKEN` | same as the previous film |
| Prefill · KV cache | `EMBED` | ditto |
| Decode loop | `ATTENTION` | ditto |
| Sampling | `PROB` | ditto |
| Stream back | `ASSISTANT` | the reply path |
| After the response | `NETWORK` | a copy going elsewhere |

The four in-box accents are **exactly** `chatgpt_message_journey`'s four, in the
same order. Same machine, seen in context — that continuity is the reason this
is a second video rather than an edit of the first.

**Colour repeats are allowed only between stations that are never adjacent and
never on screen together.** `WARN` is on the bot check and the gateway (25 units
apart), `NETWORK` on the edge and the after bay (opposite corners), `ASSISTANT`
on the orchestrator, the stream and the box frame. Check any change against the
coordinate table in `lifecycle_set.py` before making it.

### Shot widths

Declared once, in the set, and every label states which one it belongs to:

| Constant | Value | For |
|---|---|---|
| `SHOT_TIGHT` | 13.6 | a 9.6-wide in-box bay |
| `SHOT_TIGHT_OUTER` | 16.0 | a 10.0-wide band bay |
| `W_AFTER` (scene) | 20.0 | the epilogue bay, framed left so the return rail stays in shot |
| `W_TRAVEL` (scene) | 45.0 | the climb home, framed against the rail **and** the chat |
| `SHOT_WIDE` | 58.0 | the pull-back |

Type is never given a point size. `lib/typography.py` derives one from the shot
the text is read in, so a label built for `SHOT_TIGHT_OUTER` and then held at
width 20 is under-sized — that is why the after bay's `CheckList` is built with
`frame_width=W_AFTER`.

### Rules this video inherits and must not break

- Rails are built from the **shapes** (`bay`, `tile`), never the groups, and a
  rail lands *on* the thing it feeds.
- Travel paths come from `routing.join` over the drawn rails, never from centres.
- Glow halos animate on **stroke**; `set_opacity` fills them in and buries the
  bay's contents.
- Never animate a container `VGroup`'s geometry. The packet and its stamps are a
  plain list moved by a shared delta, not a `VGroup`.
- Every `self.play` takes an explicit `run_time` and a `rate_func=motion.*`.
- One `motion.FEATURE` per beat, maximum.
- The end-of-film lap's duration is `REQUEST_LAP_RUN_TIME` **in the set**, and
  the emitted token's flight home is `EMIT_RUN_TIME`, because `validate()`
  budgets its chord-clearance checks against them.
- Rails that run **inside** the `PipelineBox` must be added to the set *after*
  `self.llm`. The box frame is an opaque fill and buries anything added before
  it — which is how the loop-back rail first rendered as nothing at all.
- The pull-back's token loop is `decode_cycle()`, not `circuit()`, and it lights
  `loop_nodes` only. Lighting `nodes` on a repeating pass is the correctness bug
  this film was fixed for.

## Reviewing a change

```bash
.venv/bin/python videos/chatgpt_request_lifecycle/render.py --profile draft --no-concat
ffmpeg -i out/chatgpt_request_lifecycle/draft/videos/scene_lifecycle/480p15/TheLifecycle.mp4 \
  -vf "fps=2,scale=427:240,tile=8x12" -frames:v 1 <scratch>/grid.png
```

Then open `grid.png`, and pull full-size stills at the orchestrator beat and the
pull-back — a 427×240 tile cannot show you whether type is legible. Everything
listed in `claude-progress.txt` under "what the frames caught" was invisible to
the Evaluator and obvious in a still.
