# Tokenization: why the model never reads your words — script

**Arc 1, Episode 1.** 59.50 s nominal · 60.0 s hard cap · one continuous shot,
no cuts · 1080p60. One scene, `TheTokenizer`, in `scenes/scene_tokenization.py`.

This file is the repo's source of truth for pacing. The design record — the
reasoning behind every beat, and what the film deliberately omits — is
`docs/briefs/arc1/tokenization.md`. Where the two disagree, **this file wins**,
and §"Corrections to the brief" below says exactly where and why.

---

## Verified numbers — the block this film is built on

Every number on a chip in this film is a real `tiktoken` output, not a
placeholder and not `fake_token_id`'s invention. They live in ONE module-level
block, `scenes/tokenizer_set.py`, and every beat imports them from there.

### Provenance

`openaipublic.blob.core.windows.net` is blocked by this environment's network
policy, so the encoding files were fetched from a third-party mirror
(`pkoukk/tiktoken-go-loader`) and then **authenticated against the SHA-256
hashes hardcoded in `tiktoken_ext/openai_public.py`**:

| file | sha256 (abbrev.) | matches tiktoken's `expected_hash` |
|---|---|---|
| `cl100k_base.tiktoken` | `223921b7…865b2a7` | yes |
| `o200k_base.tiktoken` | `446a9538…cfb1a2d` | yes |

Byte-identical to what OpenAI serves. Cross-checked: `cl100k_base` encodes
`"hello world"` to `[15339, 1917]`, the documented value.

### The encoding the film names on screen

`o200k_base` (GPT-4o). `n_vocab` = **200,019** (199,998 ranks + 21 special).
Drawn as `≈ 200,000` — rounded, derived from the constant in code rather than
typed, so the two cannot drift apart.

### The sentence

```
"How many r's in strawberry?"  ->  7 tokens, o200k_base
  5299  'How'
  1991  ' many'
   428  ' r'
   885  "'s"
   306  ' in'
101830  ' strawberry'     <-- ONE token
    30  '?'
```

### The bare word

```
"strawberry"  ->  302 'st' · 1618 'raw' · 19772 'berry'
```

### What ships as illustrative

Four figures, each carrying the word on screen or named as ours:

| figure | where | how it is marked |
|---|---|---|
| the `l o w` / `l o w e r` / `n e w e s t` merge example | B3 | `worked example · not the paper's` |
| `merge 50,000` | B3's ramp | `merge 50,000 · illustrative` |
| the `128,000` context bar | B5 | `/ 128,000  illustrative` |
| `$ / 1M tokens · in · out` | B5 | the unit is drawn with **no figures**, on purpose — real prices date the film within weeks |

Everything else — the seven ids, the three-piece split, the vocabulary size — is
verified.

---

## Corrections to the brief

**1. The brief's nine-chip row is wrong.** Its beats 2 and 4 draw nine chips
with `st│raw│berry` among them. In the real sentence the word carries a leading
space, and ` strawberry` is a single vocabulary entry: **id 101830**, and the
sentence is **seven** tokens. The three-piece split exists only for the *bare*
word with no space in front of it.

The brief anticipated this and ruled on it: *"change the chips, not the claim —
the claim that must survive is 'no piece is a bare `r`'."* The claim survives in
a stronger form. It is not that the r's were split across three pieces; it is
that the whole word — all three r's — is one opaque integer, with no piece
boundary anywhere near them. B2 and B4 are respecified accordingly, and the
leading-space rule stops being a footnote: it becomes the mechanism of the
punchline, because the same ten letters are `101830` with a space in front and
`302·1618·19772` without.

**Caveat, stated plainly:** the sentence *does* contain a chip that reads `r` —
the ` r` of `r's`, token 428. It is a real token and it is drawn. It is not a
piece of `strawberry`, it is not pulsed in B1, and it is not counted; the
counter is labelled `r in "strawberry" — 3` for exactly that reason. A literal
reading of "no chip is a bare `r`" therefore does not hold on screen, and
saying so here is cheaper than a later session "fixing" a correct frame.

**2. The question is 27 characters, not 26, and contains 4 `r`s, not 3.** The
fourth is the standalone `r` in `r's`. Both the visual and the assertion are
scoped to the word: the three `r` cells **inside `strawberry`** pulse, the
standalone one does not, and the counter is labelled rather than bare. The
assertion is derived from the substring
(`row.r_count_in(WORD) == WORD.count("r") == 3`), so the copy and the number
cannot drift apart.

**3. B2's table in the plan sums to 9.70 s against a 9.50 s beat.** The final
hold is trimmed from 0.60 to 0.40. Beat boundaries are what is fixed.

**4. The closing shrink is 0.056, not the brief's ≈0.11.** The ghost circuit is
height-bound by the wide frame, so the node the bench has to fit inside is
smaller than the brief assumed. The factor is *derived* from the node radius in
`TokenizerSet.bench_shrink`, not typed, and `validate()` fails if the shrunken
bench would not fit.

**5. `scenes/props.py` is `scenes/tokenizer_props.py`.** A video's `scenes/`
directory goes on `sys.path` as a flat namespace when a deck or
`manim render <path>` loads it, and `chatgpt_request_lifecycle/scenes/props.py`
already owns the name `props`. A second `props` resolves to whichever was
imported first — which is exactly what broke the `unit` gate the first time.

**6. The SPLIT and IDS bays use `header_side="top"`, not `"left"`.** A left-hand
header caps the slot at `HEADER_SHARE` (36%) of the bay, which fitted the seven
chips at a size below `typography.MIN_READABLE`.

---

## The set

A **bench**, read left to right like a line of text, because this is one machine
doing one thing to one string. One drop-down spur underneath carries the
consequences. Arc 0's set was a plant — a clockwise circuit, because a request
travels. The change of shape is the point.

```
   ┌─────────────────────┐
   │  THE VOCABULARY     │   (0, +9), tall — sits over the table that built it
   │  WALL   ≈ 200,000   │
   └──────────┬──────────┘
              │
 QUESTION ──▶ SPLIT ──▶ TABLE ──▶ IDS ──▶ DOOR
 (−26,+2)   (−13,+2)   (0,+3)   (+13,+2) (+24,+2)
                          │
                          ▼  consequence spur
                      THE METER
                       (0,−12)
             price · context · latency
              en 7 │ hi 32 │ my 72
```

| Bay | Centre | Size | Accent | Component |
|---|---|---|---|---|
| `QUESTION` | `(−26, +2)` | 9.6 × 6.0 | `USER` | `chat_ui.ChatWindow` |
| `SPLIT` | `(−13, +2)` | 11.0 × 4.2 | `TOKEN` | `factory.Station` + `TokenStrip` |
| `TABLE` | `(0, +3)` | 10.0 × 4.6 | `ATTENTION` | `Station` + local `MergeTable` |
| `VOCAB_WALL` | `(0, +9)` | 3.6 × 4.6 | `ATTENTION` | local `VocabWall` |
| `IDS` | `(+13, +2)` | 11.0 × 4.2 | `EMBED` | `Station` + integer faces |
| `DOOR` | `(+24, +2)` | left wall at x = 22.3 | `ASSISTANT` | `factory.PipelineBox` |
| `METER` | `(0, −12)` | 14.0 × 7.0 | `WARN` | `Station` + `stacked.SegmentedBar` |

`ASSISTANT` on the `DOOR` and `TOKEN` on the `SPLIT` are deliberately the same
colours as the Arc 0 film's inference stack, in the same roles. A returning
viewer should recognise the chips in B2 as the ones that flew past in four
seconds of the last film. `ATTENTION` on both `TABLE` and `VOCAB_WALL` is the
one intended repeat — they are on screen together and read as one unit, which
is what says *the wall is the output of the table*.

### Shot widths

```
SHOT_CHAT   = 13.0   # B0
SHOT_BENCH  = 15.0   # B1, B2
SHOT_TIGHT  = 12.0   # B3, B4 entry
SHOT_IDS    = 14.0   # B4
SHOT_METER  = 18.0   # B5
SHOT_WIDE   = 60.0   # B6
```

World extent **60.5 × 26.5**; the pull-back actually needs **62.9** at
`pad = 1.2`, a 4.8% drift from `SHOT_WIDE`, well inside the 12% `validate()`
allows. Pull-back factor `62.9 / 14.22` ≈ **4.4×**.

Rails are drawn, and every travel path is built from them with `routing.join`.
`validate()` asserts the bench run clears the wall and the meter, that the spur
clears every bay it passes, the pull-back drift, that the shrunken bench fits
the ghost node, and the two token-accounting counts.

---

## Beat sheet

| Timecode | Beat | Shot |
|---|---|---|
| 0.00–5.00 | **B0 Cold open** — the strawberry question, a wrong answer, stillness | chat, W=13 |
| 5.00–11.50 | **B1 The line** — characters on the bench, the three r's once, then the wipe | pan right, W=13 → 15 |
| 11.50–21.00 | **B2 The split** — seven chips; the space; `st│raw│berry` | pan right, W=15 |
| 21.00–33.50 | **B3 The table** — the wall, then three worked merges and the list | tilt up, W=15 → 12 |
| 33.50–40.00 | **B4 The ids** — chips flip to integers, pass the model wall | pan right, W=12 → 14 |
| 40.00–51.00 | **B5 The meter** — price, context, latency; en 7 / hi 32 / my 72; `10×` | swing down, W=14 → 18 |
| 51.00–59.50 | **B6 The bench, and where it sits** — pull back, then the bench shrinks | W=60 |

**The single most important frame in the film is B1's wipe**, where the
characters go dark. Everything before it has letters; nothing after it does.
It gets the full 1.2 s and is not decorated.

---

## Per-animation budget

Every `run_time` is nominal; changing one means re-balancing its neighbours
inside the same beat. Camera moves are played **with** the action at their
destination, never before it.

### B0 — Cold open · 0.00–5.00

| t | Δ | Action |
|---|---|---|
| 0.00 | 1.30 | `StreamingBubble` reveals `There are 2 r's in "strawberry".` beside the user bubble |
| 1.30 | 0.80 | the `2` swells and turns `ERROR` |
| 2.10 | 1.00 | `wait` — complete stillness, long enough to feel wrong |
| 3.10 | 0.80 | caption `it is not bad at counting.` |
| 3.90 | 1.10 | `wait` |

### B1 — The line · 5.00–11.50

| t | Δ | Action |
|---|---|---|
| 5.00 | 1.30 | `camera.focus(split_bay, SHOT_BENCH, shift=UP*0.9)` **with** the question flying out of the bubble along the drawn rail |
| 6.30 | 0.80 | 27 character cells settle, `motion.enter` |
| 7.10 | 1.00 | the three `r` cells **inside `strawberry`** pulse `WARN`; counter `r in "strawberry" — 3` fades in |
| 8.10 | 0.70 | hold |
| 8.80 | 1.20 | **the wipe** — every cell to `FG_FAINT`, left to right, `LaggedStart`, `motion.SHARP`; the counter goes dark with them |
| 10.00 | 0.80 | caption `this is the last frame with letters in it.` |
| 10.80 | 0.70 | hold |

### B2 — The split · 11.50–21.00 *(respecified — see corrections)*

| t | Δ | Action |
|---|---|---|
| 11.50 | 1.20 | the 27 dark cells collapse toward the `SPLIT` bay |
| 12.70 | 1.20 | `TokenStrip(SENTENCE_TOKENS, token_ids=SENTENCE_IDS)` — **7** chips snap in via `FadeIn`, `LaggedStart`, `motion.SNAP` |
| 13.90 | 0.70 | hold |
| 14.60 | 0.90 | the ` strawberry` chip lifts 0.3; caption `one token. three r's inside it.` |
| 15.50 | 0.80 | hold |
| 16.30 | 0.90 | the ` many` chip enlarges to 3.4 units with its `␣` lit in `EMBED`; caption `the space belongs to the word after it` |
| 17.20 | 0.80 | hold |
| 18.00 | 1.00 | the ` many` chip returns; `st│raw│berry` fades in above the lifted chip, which dims to 0.35 |
| 19.00 | 1.00 | caption `drop the space and it is three pieces — different numbers entirely` |
| 20.00 | 0.60 | the three re-merge into the single chip; captions out |
| 20.60 | 0.40 | hold |

### B3 — The table · 21.00–33.50 *(longest beat)*

| t | Δ | Action |
|---|---|---|
| 21.00 | 1.20 | `camera.focus(vocab_wall, SHOT_TIGHT, shift=RIGHT*2.1)` — tilt up |
| 22.20 | 1.00 | wall cells build, tiny `lag_ratio`; most are sub-`MIN_READABLE` and therefore decoration, by design |
| 23.20 | 0.70 | counter `≈ 200,000` + `every piece the model can ever see` |
| 23.90 | 1.00 | hold |
| 24.90 | 1.10 | `camera.focus(table_bay, SHOT_TIGHT)` — back down |
| 26.00 | 0.70 | `l o w` / `l o w e r` / `n e w e s t` appear as loose letters |
| 26.70 | 0.90 | **merge 1** — `l`+`o` highlight `WARN`, close up, and `lo` writes itself onto the list |
| 27.60 | 0.90 | **merge 2** — `lo`+`w` → `low` |
| 28.50 | 0.90 | **merge 3** — `e`+`s` → `es` |
| 29.40 | 0.80 | hold |
| 30.20 | 4 × 0.40 | the list scrolls up out of legibility; the counter runs `merge 4` → `merge 50,000 · illustrative` |
| 31.80 | 0.80 | caption `counted, not chosen` |
| 32.60 | 0.90 | hold |

The pairs are located by what the cells currently spell, so merge 2 finds
`lo` + `w` without an index being written down anywhere.

### B4 — The ids · 33.50–40.00 *(respecified — seven, not nine)*

| t | Δ | Action |
|---|---|---|
| 33.50 | 1.20 | `camera.focus(ids_bay, SHOT_IDS)` **with** the 7 chips travelling and flipping: the text face fades up and out, the integer face fades up and in |
| 34.70 | 0.80 | integers settle in `EMBED`: `5299 · 1991 · 428 · 885 · 306 · 101830 · 30` |
| 35.50 | 0.70 | hold |
| 36.20 | 1.00 | the row slides right through the slot in the `DOOR` wall, `MoveAlongPath` on a `routing.join` path built from the drawn rail |
| 37.20 | 0.70 | far side: vectors only, no text anywhere |
| 37.90 | 0.80 | the ` strawberry` chip ghosts in at 25% with a strike-through, `101830` under it |
| 38.70 | 0.70 | caption `no letters went through` |
| 39.40 | 0.60 | hold |

The flip is a vertical fade (text face up and out, integer face up and in), not
a 3D card rotation: Manim collapses a VMobject's points at 90°, so a rotation
cannot be reversed, and the fade uses recognised arrival classes, which the deck
needs anyway.

### B5 — The meter · 40.00–51.00

| t | Δ | Action |
|---|---|---|
| 40.00 | 1.30 | `camera.focus(meter_bay, SHOT_METER)` — swing down the spur |
| 41.30 | 1.10 | three counters fill: `price $ / 1M tokens in · out`, `context ▓▓░░ / 128,000 illustrative`, `latency prefill ∝ in · decode ∝ out` |
| 42.40 | 0.80 | hold |
| 43.20 | 0.90 | English bar draws to `7` |
| 44.10 | 1.10 | Hindi bar draws to `32` |
| 45.20 | 1.40 | Burmese bar draws to `72` and **overruns the frame edge** — that is the point |
| 46.60 | 0.90 | caption `median tokens · 2,033 parallel texts · MASSIVE · cl100k_base` |
| 47.50 | 0.90 | hold |
| 48.40 | 0.90 | the three counters re-read with the Burmese figure |
| 49.30 | 0.70 | `10×` stamps in `WARN`; the caption goes out with it |
| 50.00 | 1.00 | hold |

**The caption on the bars is not optional and is not decoration.** These are
medians over a parallel corpus, not token counts for the sentence on screen;
drawn without it, the bars assert something false. It names `cl100k_base`
because that is the encoding the source analysis used, while the film's own
chips are `o200k_base`. That is not an inconsistency to "fix" by relabelling —
it is the truth about where the figure comes from.

### B6 — The bench, and where it sits · 51.00–59.50

| t | Δ | Action |
|---|---|---|
| 51.00 | 1.60 | `camera.frame_all` to the wide shot; the bay marquees cross-fade in and the meter read-out dims under them |
| 52.60 | 0.50 | `wait` — complete stillness. The film is a diagram for one moment |
| 53.10 | 2.20 | **the bench itself** scales to 0.056 and moves up-right into the ghost node — *the camera does not move*; the Arc 0 circuit assembles around it, ten faint nodes |
| 55.30 | 0.80 | the one labelled node, `TOKENIZER`, lights |
| 56.10 | 1.00 | caption `everything above happens / before the model reads a word` |
| 57.10 | 0.90 | final card: `Arc 1 · Inside the model, just enough` / `next — Attention and the KV cache` |
| 58.00 | 1.50 | hold on the finished frame |

Scaling the set rather than moving the camera is deliberate: two pull-backs in
8.5 s reads as a stumble, and the set-shrink is the gesture that says *this
whole machine is one part of that machine*. It is played as
`Transform(bench, bench.copy().scale(...))` rather than `bench.animate.scale(...)`
— a `VGroup` carries its own transparent rgba and animating one drags every
child's opacity down, while a copy has the same rgba at every node.

---

## Token accounting — the assertions that cannot be omitted

The gates compare a 16×16 luminance grid and are structurally incapable of
noticing that a correct-looking animation makes a false claim. Arc 0 shipped
such a cut with every gate green. Each of these is an `assert` in the scene:

1. **The character row is derived, never typed.**
   `len(row.cells) == len(QUESTION) == 27` and
   `row.r_count_in(WORD) == WORD.count("r") == 3`, scoped to the word.
2. **The chips and the ids are one list.** `TokenStrip` is constructed once with
   explicit `token_ids=SENTENCE_IDS`; B4 flips *that* object and builds its
   integer faces from `strip.token_ids`. There is no second list of ids
   anywhere. `len(strip.chips) == len(strip.token_ids) == 7`.
3. **The split is exactly the word.** `"".join(WORD_TOKENS) == WORD`, the lifted
   sentence chip's token is `" " + WORD`, its id is `101830`, and the three
   chips' tokens are `WORD_TOKENS`.
4. **The vocabulary counter is rounded from the constant**, not typed.
5. At import time: the seven tokens concatenate back to `QUESTION`, and the ids
   list is the same length.

---

## The deck

`slides.py` subclasses the scene and decides only where the clicks go.
**47 animations → 40 stops**, one suppressed region (B3's merge ramp,
recognised by the `RampTicker` it animates rather than by a play index).
The plan expected 45–55 stops; 40 is the honest count for a film whose beat
sheet has 47 non-wait plays, and four of them are clear-downs that merge
forward. Nothing arrives via `.animate.set_opacity` — every arrival is a
`FadeIn`, `MoveAlongPath` or `Flash`.

B6's ghost assembly and set-shrink needs no suppression: it is already a single
`self.play`.

---

## Definition of done

```bash
.venv/bin/python scripts/evaluate.py --video tokenization   # all five gates
.venv/bin/python videos/tokenization/render.py --profile final
.venv/bin/python scripts/build_slides.py tokenization
```

Measured `final` runtime: **59.500 s** (3570 frames at 60 fps), 0.500 s under
the cap. Recorded in `scenes.json`.
