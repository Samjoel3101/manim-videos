# Tokenization: why the model never reads your words — script

**Arc 1, Episode 1.** One continuous shot, no cuts, 1080p60.
**59.50 s nominal against a HARD 60.0 s cap.**

This file is the repo's own source of truth for pacing. The design record — why
each claim is what it is, and the two things a `tiktoken` pre-flight corrected —
is `docs/briefs/arc1/tokenization.md`. The narration lives in the content repo
at `videos/ai-system-design/arc1/tokenization/`.

Every `run_time` in `scenes/scene_tokenization.py` comes from the tables below,
each beat method carries its target timecode in a comment, and **the beat
boundaries are fixed**: changing one `run_time` means re-balancing its
neighbours inside the same beat, never spending a neighbouring beat's time.

---

## Token accounting — the rule that cannot be broken

Verified against `o200k_base` (n_vocab 200,019) in a pre-flight and baked into
`scenes/tokenizer_set.py` as literals. The render needs neither network access
nor `tiktoken`.

```
"How many r's in strawberry?"  →  7 tokens
     5299  'How'
     1991  ' many'
      428  ' r'
      885  "'s"
      306  ' in'
   101830  ' strawberry'      ← the whole word. one token.
       30  '?'

"strawberry"   standalone  →  302 'st' · 1618 'raw' · 19772 'berry'
" strawberry"  with space  →  101830

27 characters · 4 r's in the sentence · 3 r's inside "strawberry"
```

Two of these corrected the scripted design, and the film is better for both.
Do not reintroduce either error:

1. **` strawberry` is ONE token in this sentence.** It splits into three pieces
   only when tokenized *standalone*, without its leading space. The sentence
   produces **seven** chips, not nine, and the film's claim is therefore the
   stronger one — *one number, with nothing inside it to count*.
2. **The sentence has four `r`s; the word has three.** The `r` in `r's` is the
   fourth. Beat 1 pulses only the three inside `strawberry`, and the assertion
   counts `"strawberry".count("r")`, never the whole question.

Five assertions carry this in code, in `scenes/scene_tokenization.py` (module
level) and `scenes/tokenizer_set.py` (`validate`):

| # | Assertion | Why it exists |
|---|---|---|
| 1 | `row.r_count == "strawberry".count("r") == 3`, and `QUESTION.lower().count("r") == 4` | the two differ on purpose; the second is the trap |
| 2 | `len(strip.chips) == len(IDS) == 7`, one `TokenStrip`, built once with explicit ids | there is no second list anywhere; beat 4 flips *that* object |
| 3 | `"".join(TOKENS) == QUESTION` | fails loudly if anyone "tidies" the leading spaces |
| 4 | `"".join(SPLIT) == "strawberry"`, `len(SPLIT) == 3`, `"r" not in SPLIT` | no piece of the word IS an `r` |
| 5 | `len(row.cells) == len(QUESTION) == 27` | the row is derived, never written down |

---

## The set — a bench, not a plant

Arc 0's set was a circuit, because a request travels. This one is read left to
right like a line of text, because it is one machine doing one thing to one
string. One drop-down spur underneath carries the consequences.

```
                     ┌─────────────────────┐
                     │  THE VOCABULARY     │   (0, +8.6)
                     │  WALL   ≈ 200,000   │
                     └──────────┬──────────┘
                                │
 QUESTION ──▶ SPLIT ──▶      TABLE      ──▶ IDS ──▶ DOOR
 (−26,+2)   (−13,+2)         (0,+3)        (+13,+2) (+24,+2)
                                │
                                ▼  consequence spur
                            THE METER
                             (0,−12)
```

| Bay | Centre | Accent | Component |
|---|---|---|---|
| `QUESTION` | `(−26, +2)` | `USER` | `components.chat_ui.ChatWindow` |
| `SPLIT` | `(−13, +2)` | `TOKEN` | `factory.Station` + `tokens.TokenStrip` |
| `TABLE` | `(0, +3)` | `ATTENTION` | `Station` + local `MergeTable` |
| `VOCAB_WALL` | `(0, +8.6)` | `ATTENTION` | local `VocabWall` |
| `IDS` | `(+13, +2)` | `EMBED` | the same `TokenStrip`, flipped |
| `DOOR` | `(+24, +2)` | `ASSISTANT` | `factory.PipelineBox` + `vectors.EmbeddingGrid` |
| `METER` | `(0, −12)` | `WARN` | `Station` + `stacked.SegmentedBar` |

`ATTENTION` on both `TABLE` and `VOCAB_WALL` is the one intended accent repeat:
they are deliberately on screen together and read as one unit, which is what
says *the wall is the output of the table*. `ASSISTANT` on the `DOOR` and
`TOKEN` on the `SPLIT` are Arc 0's inference-stack accents in the same roles.

Shot widths, declared once in the set:

```python
SHOT_CHAT   = 13.0   # B0
SHOT_BENCH  = 15.0   # B1, B2
SHOT_TIGHT  = 12.0   # B3, B4 entry
SHOT_IDS    = 14.0   # B4
SHOT_METER  = 18.0   # B5
SHOT_WIDE   = 60.0   # B6
```

World extent ≈ 57.9 × 26.4, so the pull-back needs 59.93 — 0.1% off `SHOT_WIDE`,
and `validate()` fails at construction if that drifts past 12%. At that width
the frame is 33.7 tall against a 26.4-tall world, which is what keeps the bottom
of the meter bay inside the shot; `validate()` asserts that too, because the
snapshot gate cannot see a cropped bay.

---

## Beat sheet

| Timecode | Beat | Shot |
|---|---|---|
| 0.00–5.00 | **B0 Cold open** — the question, a wrong answer, stillness | chat, W=13 |
| 5.00–11.50 | **B1 The line** — characters on the bench, the three r's, the wipe | pan right, W=15 |
| 11.50–22.50 | **B2 The split** — seven chips; then the space comes off | W=15 |
| 22.50–34.00 | **B3 The table** — the wall, three worked merges, the list | tilt up, W=12 |
| 34.00–40.50 | **B4 The ids** — chips flip to integers; `101830` is the punchline | pan right, W=14 |
| 40.50–51.00 | **B5 The meter** — price, context, latency; en 7 / hi 32 / my 72 | swing down, W=18 |
| 51.00–59.50 | **B6 The bench, and where it sits** — pull back, then into one bay | W=60 |

### B0 — Cold open · 0.00–5.00 (5.00 s)

| t | Δ | Action |
|---|---|---|
| 0.00 | 1.30 | `StreamingBubble` reveals `There are 2 r's in "strawberry".` beside the question |
| 1.30 | 0.80 | the `2` flashes and turns `WARN` |
| 2.10 | 1.00 | stillness — long enough to feel wrong |
| 3.10 | 0.80 | caption `it is not bad at counting.` |
| 3.90 | 1.10 | hold |

### B1 — The line · 5.00–11.50 (6.50 s)

| t | Δ | Action |
|---|---|---|
| 5.00 | 1.30 | camera to the bench **with** the question flying out along the drawn rail |
| 6.30 | 0.80 | 27 character cells settle, `motion.enter` |
| 7.10 | 1.00 | the three `r` cells **inside `strawberry`** light in `WARN`; counter `3` |
| 8.10 | 0.70 | hold |
| 8.80 | 1.20 | **the wipe** — all 27 cells to `FG_FAINT`, left to right, `motion.SHARP` |
| 10.00 | 0.80 | caption `this is the last frame with letters in it.` |
| 10.80 | 0.70 | hold |

### B2 — The split · 11.50–22.50 (11.00 s)

| t | Δ | Action |
|---|---|---|
| 11.50 | 1.20 | the dark cells collapse toward the `SPLIT` bay |
| 12.70 | 1.20 | **seven** chips snap in, `FadeIn`, `motion.SNAP` |
| 13.90 | 0.70 | hold |
| 14.60 | 1.00 | the ` strawberry` chip lifts `0.3` and glows; caption `one word · one token` |
| 15.60 | 1.20 | hold — the film's central surprise |
| 16.80 | 0.90 | the chip fills a third of the frame, leading `␣` in `EMBED` |
| 17.70 | 0.80 | caption `the space belongs to the word` |
| 18.50 | 1.10 | **the space is stripped** — it flies off and the chip becomes `st` `raw` `berry` |
| 19.60 | 1.00 | caption `without it, three` |
| 20.60 | 0.90 | hold |
| 21.50 | 0.70 | the three return to one chip in the row; captions out |
| 22.20 | 0.30 | hold |

### B3 — The table · 22.50–34.00 (11.50 s)

| t | Δ | Action |
|---|---|---|
| 22.50 | 1.20 | tilt up to the wall; the chips carry on down the bench to the `IDS` bay |
| 23.70 | 1.00 | the wall builds — most cells sub-`MIN_READABLE`, by design |
| 24.70 | 0.70 | counter `≈ 200,000` + caption `every piece the model can ever see` |
| 25.40 | 0.70 | hold |
| 26.10 | 1.10 | back down to the table |
| 27.20 | 0.70 | `l o w` / `l o w e r` / `n e w e s t` as loose letters |
| 27.90 | 0.90 | **merge 1** — `l`+`o` → `lo`, across every row that has it |
| 28.80 | 0.90 | **merge 2** — `lo`+`w` → `low` |
| 29.70 | 0.90 | **merge 3** — `e`+`s` → `es` |
| 30.60 | 0.50 | hold |
| 31.10 | 1.60 | the list runs away — `merge 4` → `merge 50,000`. A **ramp**: `no_stops()` |
| 32.70 | 0.80 | caption `counted, not chosen` |
| 33.50 | 0.50 | hold |

The merge example is **ours**, in the shape of the BPE paper's worked example.
It is not captioned as the paper's and it does not claim to be `o200k_base`'s
first three merges, because it is not.

### B4 — The ids · 34.00–40.50 (6.50 s)

| t | Δ | Action |
|---|---|---|
| 34.00 | 1.20 | camera to the `IDS` bay **with** the chips flipping to their integers |
| 35.20 | 0.70 | the seven integers settle in `EMBED` |
| 35.90 | 0.90 | **`101830` enlarges and glows**; caption `one word · one number` |
| 36.80 | 0.80 | hold — the answer to the cold open |
| 37.60 | 0.90 | the row crosses the model wall, `MoveAlongPath` over the drawn rails |
| 38.50 | 0.70 | far side: vectors only, no text anywhere |
| 39.20 | 0.80 | caption `nothing in 101830 is an "r"` |
| 40.00 | 0.50 | hold |

### B5 — The meter · 40.50–51.00 (10.50 s)

| t | Δ | Action |
|---|---|---|
| 40.50 | 1.30 | swing down the consequence spur |
| 41.80 | 1.10 | three counters: price · context · latency |
| 42.90 | 0.70 | hold |
| 43.60 | 0.90 | English bar draws to `7` |
| 44.50 | 1.10 | Hindi bar draws to `32` |
| 45.60 | 1.40 | Burmese bar draws to `72` and **runs off the frame edge** |
| 47.00 | 0.90 | caption `median tokens · 2,033 parallel texts · MASSIVE · cl100k_base` |
| 47.90 | 0.80 | hold |
| 48.70 | 0.80 | the three counters re-read with the Burmese figure |
| 49.50 | 0.60 | `10×` stamps in `WARN` |
| 50.10 | 0.90 | hold |

**The caption on the bars is not optional and is not decoration.** These are
medians over a parallel corpus, not token counts for the sentence on screen.
Drawing them without that caption makes the film assert something false.

`$ / 1M tokens` is shown as a **unit with no figure**, on purpose: real prices
date a film within weeks. The context bar is likewise schematic and carries no
percentage — `× 10` is the only multiplier claimed anywhere in the beat, and it
is `72 / 7`.

### B6 — The bench, and where it sits · 51.00–59.50 (8.50 s)

| t | Δ | Action |
|---|---|---|
| 51.00 | 1.60 | `camera.frame_all` to `SHOT_WIDE`; every bay cross-fades to its marquee |
| 52.60 | 0.50 | stillness. The film is a diagram for one moment |
| 53.10 | 2.20 | **the bench** scales to `0.11` into the ghost node — *the camera does not move* |
| 55.30 | 0.80 | the one labelled node, `TOKENIZER`, lights |
| 56.10 | 1.00 | caption `everything above happens before the model reads a word` |
| 57.10 | 0.90 | final card: `Arc 1 · Inside the model, just enough` / `next — Attention and the KV cache` |
| 58.00 | 1.50 | hold on the finished frame |

Scaling the set rather than moving the camera is deliberate: two pull-backs in
8.5 s reads as a stumble, and the set-shrink is the gesture that says *this whole
machine is one part of that machine*.

---

## The deck

`slides.py` subclasses `Tokenization` and decides only where the clicks go. It
copies no timing. `merge_ramp()` exists as its own method purely so the deck can
wrap it in `no_stops()` — B3's scrolling list is a ramp whose *shape* is the
content, so six clicks would flatten it exactly as re-timing it would.

---

## What this film deliberately does not contain

- **Glitch tokens.** The best story in tokenization; it needs 90 s of its own.
- **WordPiece, Unigram, SentencePiece.** Named in the study notes, not the film.
- **The softmax cost of a large vocabulary.** One level too deep here.
- **Real prices.** B5 shows `$ / 1M tokens` as a unit, with no figures.
