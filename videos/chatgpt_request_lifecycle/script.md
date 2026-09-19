# What happens when you hit send — script

**59.5 seconds, one continuous shot, no cuts. Hard cap: 60.0 s.**

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

World extent ≈ 57.3 × 29.7 units, so the final pull-back is about **4.2×**
(`wide_frame_width / 14.22` = 59.34 / 14.22). It grew from 57.89 when the
loop-back rail's wide label was added in the box's right margin: 2.3% off
`SHOT_WIDE`, well inside the 12% gate, so `SHOT_WIDE` stays at 58.0 rather than
being nudged after every label. That is further out than the previous film's 3.3×
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
| 0.00–4.84 | **Client** — types, Enter, the request assembles, optimistic bubble + spinner, POST leaves | chat, W=14 → 18 |
| 4.84–9.39 | **Bot check + Edge** — proof-of-work stamp; WAF / bot score / rate limit tick; proxied to the nearest region | pan right, W=16 |
| 9.39–13.54 | **Gateway** — session ✓, plan → model ✓, quota meter fills, trace id stamped on the packet | pan right, W=16 |
| 13.54–20.29 | **Orchestrator** — conversation + memory load; the prompt assembles as a stacked bar; your 7 tokens are a sliver; route + input classifier | pan right, W=16 |
| 20.29–24.49 | **Tokenizer** — chat template markers, then the line shatters into id chips | dive to W=13.6 |
| 24.49–29.59 | **Prefill · KV cache** — the prefix is already cached; only the tail is computed | pan down, W=13.6 |
| 29.59–34.24 | **Decode loop** — 96 layers; *one token in, one pass out — the rest is cached*; your row inside a running batch | pan down, W=13.6 |
| 34.24–40.79 | **Sampling** — a score for every word it knows; temperature/top-p; one is picked — and then **the loop**: a copy of the winning token rides the loop-back rail up to the KV cache, "and round again" | pan down, W=13.6 → 16 |
| 40.79–45.19 | **Stream back** — detokenise, output safety, tool call?, SSE chunks fly home; the **first word** lands (one token, one word) | W=16 → 45 → 14 |
| 45.19–47.44 | **After** — a copy drops down the spur: persisted, billed, jobs queued | swing down-left, W=20 |
| 47.44–48.74 | **The whole plant** — pull all the way out, wide labels cross-fade in | W=58 |
| 48.74–49.24 | Hold on the whole plant, still, before anything moves in it | W=58 |
| 49.24–51.44 | **One lap, once** — a single runner crosses the plant: bot check, edge, gateway, orchestrator, tokenizer, out through the stream and home. Then the outside drops to a resting glow and never lights again. Caption: *the request crosses once* | W=58 |
| 51.44–51.94 | Outside drops to resting; caption swaps | W=58 |
| 51.94–55.78 | **Four decode cycles** — the runner laps `decode_cycle()` INSIDE the box; each lap emits one token that flies the reply rail to the chat and reveals **exactly one** more word. Caption: *one token per pass* | W=58 |
| 55.78–56.03 | Caption swap | W=58 |
| 56.03–58.37 | **Acceleration** — six more cycles, each faster than the last, six more words. Caption: *≈60 tokens a second* | W=58 |
| 58.37–59.52 | Caption out, hold on the finished answer | W=58 |

The `run_time`s sum to **59.52 s** against a 60 s cap; the measured `final` cut
is **59.40 s** — 0.12 s *under* nominal, not over. Frame quantisation does not
reliably pad this film, and planning as though it does is how you give away
headroom you actually have.

Measured, not assumed: `type_animation` issues one `wait(1/17)` per character,
and at 60 fps each is truncated to 3 frames rather than rounded up, losing
0.256 s over the opening; rounding on the other ~110 plays returns ~0.14 s. Net
−0.117 s. The real timeline therefore runs ~0.24 s ahead of these timecodes
through the middle of the film and ~0.12 s ahead by the end, which matters only
if you are pulling a still at a named timecode.

The `draft` profile at 15 fps quantises far more coarsely and reads high by a
couple of seconds — **always measure the cap against a `final` render.** The
measured figure for the shipped cut is in `scenes.json`.

### Token accounting — the rule that cannot be broken

The reply is **eleven words**, so the film shows **eleven decode cycles**: one in
close-up at the sampler beat (its word lands in the bubble at the end of the
stream beat), four explicit ones at the pull-back, and six in the acceleration.
`TheLifecycle.tokens_emitted` is the only thing that drives `answer.reveal`, it
is incremented in exactly one place, and the beat ends with an assertion that it
equals `answer.word_count`.

This is a correctness fix, not a polish pass. The shipped cut before it ran the
end-of-film runner twice around the WHOLE circuit, lighting all ten nodes on
each pass — which asserts that every token you receive is re-scored at the edge,
re-authenticated at the gateway and re-assembled by the orchestrator. It is not:
prefill runs once, and every subsequent token is one decode step that reads the
KV cache and appends to it. The same cut also revealed three words for the first
token and four for each of two further "tokens": two tokens, eight words.

Every beat method in `scenes/scene_lifecycle.py` carries its target timecode in a
comment above it; changing one `run_time` means re-balancing its neighbours.

## Narration (131 words — holds are placed for it; no voice recorded yet)

**The script was cut to the film, not the film stretched to the script.** The
previous narration here was 315 words: at 150–165 wpm that is 115–126 seconds of
speech for a 50-second film under a 60-second cap, so it needed roughly twice the
entire budget. Adding ten seconds of holds could never have closed that gap; the
only honest move was an editorial cut of about 60%. What went is everything the
picture already makes — the list of things in the request card, the names of the
sampling knobs, the itemised contents of the prompt, the jobs the epilogue
queues. What stayed is what the frame cannot say on its own: the cache, the loop,
and the asymmetry between crossing the plant once and looping inside it.

131 words is ≈50 s at 155 wpm inside a 59.5 s film, which leaves the opening, the
gaps between beats and the final hold as silence — deliberately. A line may run a
little past its own beat into the next one's slack; the two places that is
designed in are the orchestrator's line finishing over the tokenizer, and the
prefill's finishing over the decode beat.

| Beat | Words | Line |
|---|---|---|
| Client | 11 | "You hit send. Before anything else: prove you're not a bot." |
| Edge | 10 | "It clears a firewall, a bot score, a rate limit." |
| Gateway | 11 | "A gateway decides who you are and what you've paid for." |
| Orchestrator | 17 | "None of this is the model. Your question ends up the last few tokens of four thousand." |
| Tokenizer | 4 | "That's cut into tokens." |
| Prefill | 12 | "Most of this prompt is already cached. Only the tail is computed." |
| Decode | 11 | "Then one pass through the stack, sharing the machine with strangers." |
| Sampling | 17 | "One word is picked, and it goes two ways: out to you, and back into the cache." |
| Stream | 9 | "It becomes text, checked, and pushed down the wire." |
| After | 6 | "A copy is stored, counted, billed." |
| Pull-back | 23 | "The request crosses the plant once. The answer is a loop between three bays — sixty times a second. Nothing upstream is asked twice." |
| **Total** | **131** | |

Read end to end:

> You hit send. Before anything else: prove you're not a bot. It clears a
> firewall, a bot score, a rate limit. A gateway decides who you are and what
> you've paid for.
>
> None of this is the model. Your question ends up the last few tokens of four
> thousand. That's cut into tokens. Most of this prompt is already cached; only
> the tail is computed. Then one pass through the stack, sharing the machine
> with strangers.
>
> One word is picked, and it goes two ways: out to you, and back into the cache.
> It becomes text, checked, and pushed down the wire. A copy is stored, counted,
> billed.
>
> The request crosses the plant once. The answer is a loop between three bays —
> sixty times a second. Nothing upstream is asked twice.

### Where the holds are

The 9.27 s this pass added is **stillness after content lands**, never slower
motion: a camera move stretched by a third reads as sluggish, the same move
followed by a beat of stillness reads as deliberate. Every one is a bare
`self.wait(t)` in `scenes/scene_lifecycle.py` with a comment naming the line it
carries.

| Beat | Was | Added | Now | Where the hold sits |
|---|---|---|---|---|
| Client | 4.59 | +0.25 | 4.84 | after the request card lands |
| Edge | 4.20 | +0.35 | 4.55 | after all three checks are struck |
| Gateway | 3.80 | +0.35 | 4.15 | after the quota meter stops |
| Orchestrator | 5.20 | +1.55 | 6.75 | +1.00 on the emphasised sliver, +0.55 after the badges |
| Tokenizer | 3.80 | +0.40 | 4.20 | after the id chips have all arrived |
| Prefill | 3.85 | +1.25 | 5.10 | +0.75 on the emphasised tail, +0.50 on the second caption |
| Decode | 4.00 | +0.65 | 4.65 | after the batch meter stops |
| Sampling | 5.10 | +1.45 | 6.55 | +0.45 after the winner's Flash, +1.00 once the copy has joined the cache |
| Stream | 3.90 | +0.50 | 4.40 | on the first word in the bubble |
| After | 1.95 | +0.30 | 2.25 | after the ledger ticks |
| Pull-back | 9.86 | +2.22 | 12.08 | +0.50 on the whole plant before the lap, +0.60 on the lap itself, +0.72 across the four explicit cycles, +0.40 on the final frame |
| **Total** | **50.25** | **+9.27** | **59.52** | |

Three things in the pull-back were deliberately **not** touched. `CYCLES_FAST` is
a halving ramp and its shape *is* the acceleration, so stretching it would undo
the fix that put it there. No cycle was added — eleven words, eleven tokens,
asserted at the end of the beat. And `EMIT_RUN_TIME` stayed at 0.40 because
`validate()` budgets the emitted token's comet chords against it; the extra lap
time went into `REQUEST_LAP_RUN_TIME` (1.6 → 2.2), where a *slower* lap only
makes that budget finer.

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
- The end-of-film lap's `run_time` lives in the **set** as
  `REQUEST_LAP_RUN_TIME` (and the emitted token's flight home as
  `EMIT_RUN_TIME`), because `validate()` budgets its chord-clearance checks
  against them. Change them in one place or the assertions silently stop
  matching the shot they are supposed to be checking.
- **Draw order is load-bearing inside the box.** `PipelineBox.frame` is an
  opaque fill, so every rail that runs inside it — the descent, the rails between
  bays, the way out, and the loop-back — must be added to the set *after*
  `self.llm`. The first cut of the loop-back rail was added before it and
  rendered as nothing at all: a runner lapping a path with no track under it,
  and a green gate.
- **The loop-back rail is drawn, not implied.** `LOOPBACK_X = 23.25` is the
  midline of the box's 0.90-wide inner right margin, `decode_cycle()` is joined
  from the drawn rails and must CLOSE (asserted), and the rail carries a
  wide-shot label — "append K,V · next token" — in the margin outside the frame,
  mirroring the box's own side title.
- Motion blur stays off on every profile. That is recorded in `harness.json`
  with its reason; it is not an oversight.
