# What happens when you hit send — script

**45 seconds, one continuous shot, no cuts.**

The extended cut of `chatgpt_message_journey`. That film showed the model; this
one shows the whole plant the model sits inside — client, edge, gateway,
orchestrator, tokenizer, prefill, decode, sampler, streaming, and the fan-out
that happens after the answer is already on your screen.

The two films share the `/lib` vocabulary, the palette, and the four in-box
station colours **on purpose**. A returning viewer should recognise the column in
the middle of this set as the machine they already walked through, now seen in
context. `chatgpt_message_journey` is not modified by this video and must not be.

## The set

One clockwise circuit around a 16:9-shaped world: out along the top, down the
right into the machine, back along the bottom, and up the left side to the
client. Coordinates are bay centres; the full table lives in
`scenes/lifecycle_set.py`, which is the only place they may be edited.

```
   CLIENT ──▶ [✓] ──▶  EDGE  ──▶ GATEWAY ──▶ ORCHESTRATOR
  (−24,+9)   bot     (−8,+9)     (+5,+9)      (+18,+9)
     ▲      check                                  │
     │     (−16,+9)                                ▼
     │                          ┌─ THE INFERENCE STACK ─┐   x 12.3…23.7
     │                          │  TOKENIZER    (+18, +0.85)
     │                          │  PREFILL·KV   (+18, −1.85)
     │                          │  DECODE LOOP  (+18, −4.55)
     │                          │  SAMPLER      (+18, −7.25)
     │                          └───────────┬───────────┘   y +3.6…−9.2
     │                                      ▼
     └───────────◀──────────── STREAM BACK ◀┘
       x = −30.5   │            (+5,−12)
                   ▼ fan-out spur
                 AFTER  (−20,−16)
```

World extent ≈ 55.9 × 29.7 units, so the final pull-back is about **4.1×**
(`wide_frame_width / 14.22` = 57.89 / 14.22). That is further out than the previous film's 3.3×
and is affordable for exactly one reason: type is sized as a share of frame
height (`lib/typography.py`), so every wide-shot label grows with the pull-back
instead of shrinking into it. `SHOT_WIDE = 58.0`, and `LifecycleSet.validate()`
fails at construction if the real figure drifts more than 12% from it.

## The through-line

One payload, never destroyed, only transformed — this is what makes it read as a
factory rather than a slideshow:

> typed text → a request with its metadata → a stamped packet → a scored packet →
> a traced packet → **a sliver at the bottom of a 3,900-token prompt** → token
> chips with ids → a cached prefix plus a short new tail → one row in a running
> batch → a bar in a distribution → one token → SSE chunks → words in the bubble
> → a row in a ledger

The question is `What happens when I hit send?` and the answer is
`A dozen machines touch it before the first word comes back.` The sampler beat
picks ` A` as the winning token, which is the first word of that answer — keep
the distribution and the reply consistent, because a mismatch there is exactly
the kind of single-token error the snapshot gate cannot see.

## Beat sheet

| Timecode | Beat | Shot |
|---|---|---|
| 0.00–4.59 | **Client** — types, Enter, the request assembles, optimistic bubble + spinner, POST leaves | chat, W=14 → 18 |
| 4.59–8.79 | **Bot check + Edge** — proof-of-work stamp; WAF / bot score / rate limit tick; proxied to the nearest region | pan right, W=16 |
| 8.79–12.59 | **Gateway** — session ✓, plan → model ✓, quota meter fills, trace id stamped on the packet | pan right, W=16 |
| 12.59–17.79 | **Orchestrator** — conversation + memory load; the prompt assembles as a stacked bar; your 7 tokens are a sliver; route + input classifier | pan right, W=16 |
| 17.79–21.59 | **Tokenizer** — chat template markers, then the line shatters into id chips | dive to W=13.6 |
| 21.59–25.44 | **Prefill · KV cache** — the prefix is already cached; only the tail is computed | pan down, W=13.6 |
| 25.44–29.44 | **Decode loop** — 96 layers, one token per step, your row inside a running batch | pan down, W=13.6 |
| 29.44–32.84 | **Sampling** — a score for every word it knows; temperature/top-p; one is picked | pan down, W=13.6 |
| 32.84–36.74 | **Stream back** — detokenise, output safety, tool call?, SSE chunks fly home; first words land | W=16 → 45 → 14 |
| 36.74–39.24 | **After** — a copy drops down the spur: persisted, billed, jobs queued | swing down-left, W=20 |
| 39.24–44.34 | **The whole plant** — pull all the way out, wide labels cross-fade in, two more tokens run the circuit, the reply completes | W=58 |

The `run_time`s sum to **44.34 s** against a 45 s budget. The rendered cut is a
little longer than that — Manim rounds every play up to a whole frame and there
are about seventy of them, which costs ~0.8 s at 60 fps and ~1.9 s at 15 fps. The
measured figure for the shipped `final` cut is in `scenes.json`; the draft
profile, being 15 fps, always reads high.

Every beat method in `scenes/scene_lifecycle.py` carries its target timecode in a
comment above it; changing one `run_time` means re-balancing its neighbours.

## Narration (no voice-over pass in this cut)

> You hit send. Before anything reaches a GPU, your browser has already built a
> request — your text, the conversation it belongs to, which model you are
> allowed to use — and proved it is not a bot.
>
> It lands at the edge: a firewall, a bot score, a rate limit. Then a gateway,
> which works out who you are, what you have paid for, and how much you have
> left.
>
> Now the part that is not the model at all. The orchestrator loads your
> conversation, your memory, your instructions, and builds the prompt: a system
> message, tool definitions, everything the model needs to behave. Your question
> is the last few tokens of about four thousand.
>
> That gets cut into tokens. Most of it the machine has seen before — the shared
> prefix is already in cache, so only the tail is computed. Then the decode loop:
> one token per step, your request riding in a batch with strangers'.
>
> Every step produces a score for every word it knows. One gets picked, turned
> back into text, checked, and pushed down the wire as it is written — which is
> why the answer arrives a word at a time.
>
> And when it finishes, a copy goes somewhere else entirely: stored, counted,
> billed, and handed to the jobs that title the chat and remember what you said.

## Notes for editing

- **The shot widths are constants, not preferences.** `W_SERVICE = 16.0` is the
  floor that clears a 10.0-wide band bay at 16:9 with margin; `W_TIGHT = 13.6`
  is the floor for a 9.6-wide in-box bay. Anything smaller crops the bottom of a
  bay and no test can see it — look at the frames.
- **Colour repeats are allowed only between stations that are never adjacent and
  never on screen together.** `theme.WARN` is on the bot check and the gateway,
  `theme.NETWORK` on the edge and the after bay, `theme.ASSISTANT` on the
  orchestrator, the stream and the box frame. Check any change against the
  coordinate table before making it.
- The four in-box accents (TOKEN, EMBED, ATTENTION, PROB) are **exactly** the
  previous film's four, in the same order. That continuity is the point.
- `RequestCard` is a close-up-only prop: it is faded out at the end of beat 1
  because it would be litter in the pull-back, which is also why it is not part
  of `LifecycleSet.everything` and does not affect `SHOT_WIDE`.
- The end-of-film loop's `run_time` lives in the **set** as
  `LOOP_RUN_TIME`, because `validate()` budgets its chord-clearance check
  against it. Change it in one place or the assertion silently stops matching
  the shot it is supposed to be checking.
- Motion blur stays off on every profile. That is recorded in `harness.json`
  with its reason; it is not an oversight.
