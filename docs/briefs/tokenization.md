# Build brief — `tokenization`

**Arc 1, Episode 1 of the AI System Design series.**
**59.5 s nominal · 60.0 s hard cap · one continuous shot, no cuts · 1080p60.**

This file is the generation prompt. It is complete enough to build from without
reading anything else in the series, and it is written to be handed to an
implementing subagent whole.

Read the root `AGENTS.md` first — it governs `/lib`, the promotion rule, the
Evaluator and the protected paths. Read `docs/slides.md` before writing a beat,
because every beat here ships as a click-deck stop as well as a film frame.
`.claude/skills/factory-video/` carries the continuous-shot recipe; this set is
a bench rather than a plant, but the motion language is identical.

Narration, the reasoning behind every claim, and the reference list live in the
content repo: `Samjoel3101/content` →
`videos/ai-system-design/content/tokenization/`. The beat numbers B0–B6 are the
same in all three documents.

---

## Step 0 — scaffold

```bash
./init.sh
.venv/bin/python scripts/new_video.py tokenization \
    --title "Tokenization: why the model never reads your words"
```

Then copy the **Beat sheet**, **The set** and **Token accounting** sections of
this file into `videos/tokenization/script.md`, which is the repo's own source
of truth for pacing. This brief stays here as the design record.

---

## Step 1 — blocking pre-flight, before a single chip is drawn

Four numbers appear on screen. **Three of them are currently placeholders and
the film must not ship with placeholders on chips.** Run this first, in an
environment with network access, and paste the real output into
`videos/tokenization/script.md`:

```bash
.venv/bin/pip install tiktoken
.venv/bin/python - <<'PY'
import tiktoken
enc = tiktoken.get_encoding("o200k_base")   # GPT-4o; swap if you name another
print("n_vocab:", enc.n_vocab)
for s in ["How many r's in strawberry?", "strawberry"]:
    ids = enc.encode(s)
    print(repr(s), len(ids))
    for i in ids:
        print("   ", i, repr(enc.decode([i])))
PY
```

Decide from the output and record the decision in `script.md`:

1. **Which encoding the film names on screen.** Pick one and caption it. Mixing
   `cl100k_base` counts with an `o200k_base` vocabulary size is the exact kind
   of error the snapshot gate cannot see.
2. **The real token ids** for beat 4's chips. `TokenStrip` will invent plausible
   ids via `fake_token_id` if you don't supply them — do **not** let it here.
   Pass `token_ids=[...]` explicitly with the verified values.
3. **The real split of `strawberry`.** The brief assumes `st · raw · berry`. If
   the chosen encoding splits it differently, **change the chips, not the
   claim** — the claim that must survive is "no piece is a bare `r`", which
   holds under every GPT-family encoding.
4. **The vocabulary counter.** Round and caption it: `≈ 200,000`, not a precise
   figure that may or may not include special tokens.

If network access is unavailable, every affected number must carry a visible
`illustrative` caption on screen and the fact must be recorded in
`claude-progress.txt`. Do not silently ship an invented token id — the whole
film is an argument that these specific integers are what the model receives.

---

## The set — `scenes/tokenizer_set.py`

Arc 0's set was a plant: a clockwise circuit, because a request travels. This
set is a **bench**, read left to right like a line of text, because this is one
machine doing one thing to one string. One drop-down spur underneath carries the
consequences.

All coordinates live in this module and nowhere else. `validate()` re-derives
the wall and box edges from the drawn mobjects rather than trusting the numbers
written here.

```
   ┌─────────────────────┐
   │  THE VOCABULARY     │   (0, +9), tall — sits over the table that built it
   │  WALL  ≈200,000     │
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

| Bay | Centre | Accent | Component | What it holds |
|---|---|---|---|---|
| `QUESTION` | `(−26, +2)` | `USER` | `components.chat_ui.ChatWindow` | the cold open, then the character row |
| `SPLIT` | `(−13, +2)` | `TOKEN` | `components.factory.Station` + `TokenStrip` | the chips |
| `TABLE` | `(0, +3)` | `ATTENTION` | `Station` + local `MergeTable` prop | the worked merges, the ordered list |
| `VOCAB_WALL` | `(0, +9)` | `ATTENTION` | local `VocabWall` prop | the dense column, the counter |
| `IDS` | `(+13, +2)` | `EMBED` | `Station` + `TokenStrip(show_ids=True)` | the integers |
| `DOOR` | `(+24, +2)` | `ASSISTANT` | `components.factory.PipelineBox` (left wall only) | the model boundary |
| `METER` | `(0, −12)` | `WARN` | `Station` + `components.stacked.SegmentedBar` | three counters, three language bars |

Rails are drawn with `factory.rail_between` and every travel path is built from
the drawn rails via `routing.join` — never from bay centres. `validate()` calls
`routing.assert_path_clears` on the question → split → table → ids → door run
and on the table → meter spur.

### Accent policy

`ASSISTANT` on the `DOOR` and `TOKEN` on the `SPLIT` are **deliberately the same
colours as the Arc 0 film's inference stack**, in the same roles. A returning
viewer should recognise the chips in beat 2 as the same chips that flew past in
four seconds of the last film, now slowed down enough to read. Do not change
them. `chatgpt_request_lifecycle` and `chatgpt_message_journey` are not modified
by this video.

Colour repeats are allowed only between bays that are never adjacent and never
on screen together. `ATTENTION` is on `TABLE` and `VOCAB_WALL`, which are
deliberately on screen together and read as one unit — that is the one intended
repeat, and it is what says *the wall is the output of the table*.

### Shot widths

Declared once, in the set. Every label states which shot it belongs to, and type
is sized against that shot via `lib/typography.py` — never a raw `font_size=`.

```python
SHOT_CHAT   = 13.0   # B0
SHOT_BENCH  = 15.0   # B1, B2
SHOT_TIGHT  = 12.0   # B3, B4 entry
SHOT_IDS    = 14.0   # B4
SHOT_METER  = 18.0   # B5
SHOT_WIDE   = 60.0   # B6
```

World extent ≈ **59 × 30** units, so the closing pull-back is
`SHOT_WIDE / 14.22` ≈ **4.22×** — deliberately the same factor as the Arc 0
film, so the two episodes end on the same gesture. `validate()` fails at
construction if the real extent drifts more than 12% from `SHOT_WIDE`.

At `SHOT_WIDE` the frame is 60 wide by 33.7 high, which clears the 30-unit
vertical extent. Check this after any layout change: **a shot that crops the
bottom of the meter bay is the commonest bug in this format, and the snapshot
gate cannot see it.**

---

## The through-line

One payload, never destroyed, only transformed. This is the device that makes a
walk down a bench read as a machine rather than a slideshow, and every beat is a
link in it:

> a typed question → a row of characters → **the characters going dark** →
> chips with no letters in them → an ordered merge list → a row of integers →
> a number on a meter → a bar beside Hindi and Burmese → one small bay in a
> plant the viewer has already walked through

The question is `How many r's in strawberry?` and the film's answer is not a
number — it is `st · raw · berry`. Three pieces, no letters, nothing to count.

**The single most important frame in the film is beat 1's wipe**, where the
characters go dark. Everything before it has letters; nothing after it does.
If that moment does not land, the film does not work. Give it the full 1.2 s and
do not decorate it.

---

## Beat sheet

| Timecode | Beat | Shot |
|---|---|---|
| 0.00–5.00 | **B0 Cold open** — the strawberry question, a wrong answer, stillness | chat, W=13 |
| 5.00–11.50 | **B1 The line** — characters on the bench, the three r's visible once, then the wipe | pan right, W=13 → 15 |
| 11.50–21.00 | **B2 The split** — chips snap in; `st\|raw\|berry`; the leading space | pan right, W=15 |
| 21.00–33.50 | **B3 The table** — the vocabulary wall, then three worked merges and the ordered list | tilt up, W=15 → 12 |
| 33.50–40.00 | **B4 The ids** — chips flip to integers, pass the model wall | pan right, W=12 → 14 |
| 40.00–51.00 | **B5 The meter** — price, context, latency; en 7 / hi 32 / my 72; `10×` | swing down, W=14 → 18 |
| 51.00–59.50 | **B6 The bench, and where it sits** — pull back, then the bench shrinks into one bay of the Arc 0 plant | W=60 |

Nominal total **59.50 s** against a 60.0 s cap. The Arc 0 film measured 0.12 s
*under* nominal at `final`, so do not assume frame quantisation pads this.
**Always measure the cap against a `final` render** — the `draft` profile at
15 fps quantises coarsely and reads high by a couple of seconds. Record the
measured figure in `scenes.json`.

---

## Per-animation time budget

Every `run_time` below is nominal. Changing one means re-balancing its
neighbours inside the same beat — the beat boundaries are fixed. Each beat
method in `scenes/scene_tokenization.py` carries its target timecode in a
comment above it.

Camera moves are played **with** the action at their destination, not before it.
That is why `camera.focus` returns an animation rather than playing one.

### B0 — Cold open · 0.00–5.00 (5.00 s)

| t | Δ | Action |
|---|---|---|
| 0.00 | 1.30 | `StreamingBubble` reveals `There are 2 r's in "strawberry".` beside the existing user bubble |
| 1.30 | 0.80 | `effects.pulse` on the `2` |
| 2.10 | 1.00 | `self.wait(1.0)` — complete stillness, long enough to feel wrong |
| 3.10 | 0.80 | caption `it is not bad at counting.` — `FadeIn`, `typography.text("caption", SHOT_CHAT)`, `FG_MUTED` |
| 3.90 | 1.10 | `self.wait(1.1)` |

### B1 — The line · 5.00–11.50 (6.50 s)

| t | Δ | Action |
|---|---|---|
| 5.00 | 1.30 | `camera.focus(split_bay, width=SHOT_BENCH)` **played with** the question flying out of the bubble onto the bench |
| 6.30 | 0.80 | 26 character cells settle, `motion.enter` with `lag=motion.LAG` |
| 7.10 | 1.00 | the three `r` cells pulse in `WARN`; counter `3` `FadeIn` |
| 8.10 | 0.70 | hold |
| 8.80 | 1.20 | **the wipe** — every cell drops to `FG_FAINT`, left to right, `LaggedStart`, `rate_func=motion.SHARP`; the counter goes dark with them |
| 10.00 | 0.80 | caption `this is the last frame with letters in it.` |
| 10.80 | 0.70 | hold |

### B2 — The split · 11.50–21.00 (9.50 s)

| t | Δ | Action |
|---|---|---|
| 11.50 | 1.20 | dark cells collapse toward the `SPLIT` bay |
| 12.70 | 1.20 | `TokenStrip` chips snap in, `LaggedStart`, `rate_func=motion.SNAP` — arrive via `FadeIn`, never `.animate.set_opacity` |
| 13.90 | 0.70 | hold |
| 14.60 | 0.90 | the `st` / `raw` / `berry` chips lift `0.3` and hold; caption `strawberry · three pieces` |
| 15.50 | 1.00 | hold |
| 16.50 | 0.90 | the ` many` chip scales to fill ~a quarter of the frame |
| 17.40 | 0.80 | its `␣` glyph lights in `EMBED` (`TokenChip(show_space=True)`); caption `the space belongs to the word after it` |
| 18.20 | 1.20 | hold |
| 19.40 | 0.90 | chip returns to the row; captions out |
| 20.30 | 0.70 | hold |

### B3 — The table · 21.00–33.50 (12.50 s) — *longest beat*

| t | Δ | Action |
|---|---|---|
| 21.00 | 1.20 | `camera.focus(vocab_wall, width=SHOT_TIGHT)` — tilt up |
| 22.20 | 1.00 | wall cells build, `LaggedStart` with a very small `lag_ratio`; most cells sub-`MIN_READABLE` and therefore decoration, by design |
| 23.20 | 0.70 | counter `≈ 200,000` + caption `every piece the model can ever see` |
| 23.90 | 1.00 | hold |
| 24.90 | 1.10 | `camera.focus(table_bay, width=SHOT_TIGHT)` — back down |
| 26.00 | 0.70 | `l o w` / `l o w e r` / `n e w e s t` appear as loose letters |
| 26.70 | 0.90 | **merge 1** — the `l`+`o` pairs highlight in `WARN` across all rows, snap together into `lo`, and `lo` writes itself onto the ordered list |
| 27.60 | 0.90 | **merge 2** — `lo`+`w` → `low` |
| 28.50 | 0.90 | **merge 3** — `e`+`s` → `es` |
| 29.40 | 0.80 | hold |
| 30.20 | 1.60 | the list scrolls upward, accelerating out of legibility; its counter runs `merge 4` → `merge 50,000` |
| 31.80 | 0.80 | caption `counted, not chosen` |
| 32.60 | 0.90 | hold |

The merge example is **ours**, in the shape of the BPE paper's worked example.
Do not caption it as the paper's.

### B4 — The ids · 33.50–40.00 (6.50 s)

| t | Δ | Action |
|---|---|---|
| 33.50 | 1.20 | `camera.focus(ids_bay, width=SHOT_IDS)` **played with** the chips flipping — text face rotates out, integer face rotates in |
| 34.70 | 0.80 | integers settle in `EMBED` |
| 35.50 | 0.70 | hold |
| 36.20 | 1.00 | the row slides right through a narrow slot in the `DOOR` wall, `MoveAlongPath` on a `routing.join` path |
| 37.20 | 0.70 | far side of the wall: vectors only, no text anywhere |
| 37.90 | 0.80 | the three `strawberry` chips ghost in above the row at 25% and a strike-through crosses them |
| 38.70 | 0.70 | caption `no letters went through` |
| 39.40 | 0.60 | hold |

### B5 — The meter · 40.00–51.00 (11.00 s)

| t | Δ | Action |
|---|---|---|
| 40.00 | 1.30 | `camera.focus(meter_bay, width=SHOT_METER)` — swing down the spur |
| 41.30 | 1.10 | three counters fill: `price $ / 1M tokens in · out`, `context ███░░ / 128,000`, `latency prefill ∝ in · decode ∝ out` |
| 42.40 | 0.80 | hold |
| 43.20 | 0.90 | English bar draws to `7` |
| 44.10 | 1.10 | Hindi bar draws to `32` |
| 45.20 | 1.40 | Burmese bar draws to `72` and **overruns the frame edge** — let it leave the shot; that is the point |
| 46.60 | 0.90 | caption `median tokens · 2,033 parallel texts · MASSIVE · cl100k_base` |
| 47.50 | 0.90 | hold |
| 48.40 | 0.90 | the three counters above re-read with the Burmese figure |
| 49.30 | 0.70 | `10×` stamps across the bay in `WARN` |
| 50.00 | 1.00 | hold |

**The caption on the bars is not optional and is not decoration.** These are
medians over a parallel corpus, not token counts for the sentence on screen.
Drawing them without that caption makes the film assert something false.

### B6 — The bench, and where it sits · 51.00–59.50 (8.50 s)

| t | Δ | Action |
|---|---|---|
| 51.00 | 1.60 | `camera.frame_all(...)` to `SHOT_WIDE`; five bay marquees cross-fade in at `typography` role `display` |
| 52.60 | 0.50 | `self.wait(0.5)` — complete stillness. The film is a diagram for one moment |
| 53.10 | 2.20 | **the bench itself** scales to ≈`0.11` and moves up-right into the ghost node — *the camera does not move*; simultaneously the Arc 0 circuit assembles around it at 15% opacity, ten unlabelled nodes |
| 55.30 | 0.80 | the one labelled node, `TOKENIZER`, lights |
| 56.10 | 1.00 | caption `everything above happens before the model reads a word` |
| 57.10 | 0.90 | final card: `Arc 1 · Inside the model, just enough` / `next — Attention and the KV cache` |
| 58.00 | 1.50 | hold on the finished frame |

**The ghost circuit is a local prop in `scenes/props.py`** — ten faint dots in
the Arc 0 circuit shape with one label. Do **not** import
`chatgpt_request_lifecycle.scenes.lifecycle_set`: videos are self-contained, and
the ghost is a gesture at that film, not a rendering of it. Ten dots and one
label is the whole prop; if it takes more than forty lines, it is being
over-built.

Scaling the set rather than moving the camera is deliberate. Two camera
pull-backs in 8.5 s reads as a stumble, and the set-shrink is the gesture that
actually says *this whole machine is one part of that machine*.

---

## Components

**Check `/lib/components/` before writing any new visual.** Extend or
parametrize what is there. A new chip variant is a keyword argument, not a
second class.

Reuse as-is:

| Need | Use |
|---|---|
| chat window, bubbles, streaming reveal | `components.chat_ui.ChatWindow`, `ChatBubble`, `StreamingBubble` |
| token chips, with or without ids and space glyphs | `components.tokens.TokenStrip(source, token_ids=..., show_ids=True, show_space=True)` |
| bay frames, rails, the model wall | `components.factory.Station`, `PipelineBox`, `rail_between` |
| the context-window bar | `components.stacked.SegmentedBar` |
| glow, pulse, arrival | `lib.effects` |
| travel paths | `routing.join` over the drawn rails |

Write locally in `scenes/props.py`, one-offs only:

- **`CharacterRow`** — the 26 individual character cells of B1, with a
  `wipe_dark()` method. One video needs this; it does not go in `/lib`.
- **`MergeTable`** — the three worked rows plus the scrolling ordered list.
- **`VocabWall`** — the dense column and its counter.
- **`GhostCircuit`** — B6's ten faint nodes.

**Promote to `/lib` only if a second scene needs it.** If `CharacterRow` turns
out to be wanted by the "Forcing JSON" episode — which is plausible, since
constrained decoding is exactly the character/token mismatch — that is the
moment to promote it, and it gets a structural test in `/tests/` at the same
time. Not before.

Pull colour from `lib/theme.py`, easing from `lib/motion.py`, type from
`lib/typography.py`. A hex string is a bug; so is a `self.play` without
`rate_func=motion.*`; so is a raw `font_size=`.

---

## The deck

Every video ships two outputs from one choreography. `videos/tokenization/
slides.py` subclasses the scene and decides only where the clicks go — it never
copies a timing. `tests/test_slides_convention.py` enforces this inside the
`unit` gate.

This film was authored to convert cleanly, and three things in it are there for
the deck as much as for the film:

- **Every beat clears its own props.** B2's enlarged chip returns to the row;
  B5's captions go out before B6 begins.
- **Narration holds sit after content arrives**, not after a clear-down, so a
  stop lands on a full frame rather than an empty one.
- **B3's scrolling merge list and B6's ghost assembly are ramps** and belong in
  `no_stops()` — they are texture between two readable states, not two states.

Expect roughly 45–55 stops. Probe before building:

```bash
.venv/bin/python scripts/build_slides.py tokenization --probe
```

---

## Token accounting — the rule that cannot be broken

Arc 0 shipped a cut that revealed more words than it had emitted tokens, and
every automated gate passed. The gates compare a 16×16 luminance grid; they are
structurally incapable of noticing that a correct-looking animation is making a
false claim. This film has three equivalents, and each gets an assertion in the
scene rather than a careful eye:

1. **The character count is one number.** `CharacterRow` derives its cells from
   the question string. The beat ends with
   `assert row.r_count == question.lower().count("r")` — if the copy on screen
   ever changes, the `3` changes with it or the render fails.
2. **The chips and the ids are one list.** `TokenStrip` is constructed once,
   with explicit verified `token_ids`, and B4 flips *that* object. There is no
   second list of ids anywhere in the scene. Assert
   `len(strip.chips) == len(strip.token_ids)`.
3. **`strawberry` is exactly the chips that spell it.** Assert that the chips
   the film lifts in B2 and strikes through in B4 are the same objects, and
   that `"".join(c.token for c in strawberry_chips) == "strawberry"`. If the
   verified encoding splits it into four pieces rather than three, this
   assertion fails loudly and the caption gets fixed — which is the point.

None of these are polish. Each is a place where the film could pass every gate
while asserting something untrue.

---

## Definition of done

```bash
.venv/bin/python scripts/evaluate.py --skip render              # inner loop
.venv/bin/python scripts/evaluate.py --video tokenization       # full
.venv/bin/python videos/tokenization/render.py --profile final
.venv/bin/python scripts/build_slides.py tokenization
```

Green Evaluator is necessary and not sufficient. Before flipping anything to
done in `feature_list.json`:

1. **Measure the `final` cut** and confirm it is under 60.0 s. Record the
   measured figure in `scenes.json`.
2. **Pull frames and look at them.** `ffmpeg -i <cut> -vf fps=2 frames/%03d.png`,
   then actually read the images. Specifically check:
   - the wipe at ~9.5 s — do all 26 cells go dark, and does the `3` go with them?
   - the chips at ~14 s — is the split what the pre-flight said it is, and is
     any chip a bare `r`? (It must not be.)
   - the caption at ~47 s — is the MASSIVE/median caption legible at
     `SHOT_METER`, or has it dropped under `MIN_READABLE`?
   - the wide shot at ~52 s — is the bottom of the meter bay inside the frame?
   - the ghost at ~56 s — is the bench actually *inside* the `TOKENIZER` node,
     or merely near it?
3. **Read every on-screen string once, character by character.** The snapshot
   gate cannot see a single-glyph typo and this film is dense with numerals.
4. Append to `claude-progress.txt`, including which numbers were verified
   against `tiktoken` and which shipped as illustrative.

---

## What this film deliberately does not contain

Stated so a later session does not "helpfully" add them back:

- **Glitch tokens** (`SolidGoldMagikarp`). The best story in tokenization, and
  it needs 90 s of its own. It gets a separate short. Adding it here costs the
  pricing punchline, which is what Arc 1 needs before the KV cache episode.
- **WordPiece, Unigram, SentencePiece.** Named in the study notes, not in the
  film. The arc is "inside the model, just enough"; three algorithm variants is
  not just enough, it is a lecture.
- **The softmax cost of a large vocabulary.** One level too deep here; the
  memory half of it arrives naturally in the KV cache episode.
- **Real prices.** B5 shows `$ / 1M tokens` as a *unit* with no figures, on
  purpose. Real prices date the film within weeks.
