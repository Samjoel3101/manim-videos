# Tokenization: why the model never reads your words

Video project. Read the root `AGENTS.md` first — it governs /lib and the
promotion rule. This file covers only what is specific to this video.

## Where things are

- `script.md` — narration and beat timings. The source of truth for pacing.
- `feature_list.json` — one entry per scene. Status flags live here, not in prose.
- `claude-progress.txt` — what the last session did, tried, and left broken.
- `scenes.json` — the render manifest: scene order, module, duration budget.
- `scenes/` — one module per scene. Import from `/lib`; keep one-offs local.
- `render.py` — renders every scene in manifest order and concatenates.
- `slides.py` — the click-advanced deck of this film. Subclasses the scene;
  copies no timings. Built with `scripts/build_slides.py tokenization`.

## Both outputs

Every scene here is authored for the continuous film **and** for the deck. The
deck is not a second edit — it inherits the choreography and only decides where
the clicks go. Read `docs/slides.md` → "Authoring rules" before writing a beat;
the short version is that a bare `self.wait()` extends a slide rather than
costing a click, each beat clears its own props, content arrives via `FadeIn`
and friends rather than `.animate.set_opacity`, and a ramp goes in `no_stops()`.
`tests/test_slides_convention.py` fails the `unit` gate if this file's deck is
missing or has drifted from the film.

## Working on this video

1. `./init.sh` from the repo root.
2. Read `claude-progress.txt`, then `feature_list.json`; take the highest-priority
   `failing` scene, not the easiest one.
3. Build the scene. Reuse `/lib` components; promote a local one only under the
   root AGENTS.md rule.
4. `.venv/bin/python scripts/evaluate.py --video tokenization --scene <SceneClass>`
5. Only when that is green, flip the scene's status in `feature_list.json` and
   append to `claude-progress.txt`.

## Visual conventions for this video

**The set is a bench, not a plant.** Read left to right like a line of text,
because this is one machine doing one thing to one string. One spur drops out of
the bottom of the merge table to the meter, and that is the only change of
direction in the film. Everything is in `scenes/tokenizer_set.py`; a coordinate
anywhere else is a bug.

**Accents, and the one intended repeat.** `TOKEN` on `SPLIT` and `ASSISTANT` on
the `DOOR` are Arc 0's inference-stack accents in the same roles, deliberately —
a returning viewer should recognise the chips in beat 2. `ATTENTION` is on both
`TABLE` and `VOCAB_WALL`, which are on screen together on purpose and read as one
unit: that is what says *the wall is the output of the table*. Do not change
either, and do not change `chatgpt_request_lifecycle` to match anything here.

**The through-line is one payload, never destroyed.** A question, a row of
characters, the characters going dark, chips with no letters in them, an ordered
merge list, a row of integers, a number on a meter, a bar beside Hindi and
Burmese, one small bay in a plant the viewer has already walked through. The
chips and the ids are literally one `TokenStrip`, built once in the set.

**Beat 1's wipe is the film.** Everything before it has letters in it and nothing
after it does. It gets the full 1.2s, nothing else moves during it, and it is not
decorated.

**Numbers are verified or captioned as illustrative, never neither.** The token
ids come from an `o200k_base` pre-flight and are baked in as literals. Beat 5's
language bars are medians over a parallel corpus and say so on screen — that
caption is load-bearing, not decoration. The merge example and the context bar
are illustrative and claim nothing. There are no real prices anywhere, on
purpose.

**Two traps this film paid for, recorded in `claude-progress.txt`:** `props.py`
cannot be imported by bare name in this repo, and `FadeIn` animates up to a
mobject's *current* opacity, so nothing arriving later may be parked at zero.
