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
because this is one machine doing one thing to one string. One drop-down spur
underneath carries the consequences. Arc 0's circuit shape is deliberately not
reused; the change of shape is part of what the episode says.

**Colour is inherited, not re-chosen.** `TOKEN` on the `SPLIT` bay and
`ASSISTANT` on the `DOOR` are the same colours, in the same roles, as the Arc 0
film's inference stack — a returning viewer should recognise the chips. The one
intended repeat inside this film is `ATTENTION` on both `TABLE` and
`VOCAB_WALL`: they are on screen together and read as one unit, which is what
says *the wall is the output of the table*.

**The through-line is one payload, never destroyed.** A typed question becomes a
row of characters, the characters go dark, chips arrive with no letters in them,
the chips become integers, the integers cross the model wall as vectors, and the
whole bench ends up as one node of the plant from the last episode. The single
most important frame is B1's wipe at ~9.5s. It is not decorated and it is not
shortened.

**Every number on screen is asserted in code, not proof-read.** The character
row derives its cells from the question string; the chips and the ids are one
`TokenStrip`; the vocabulary counter is rounded from the constant. See
`script.md` → "Token accounting". The snapshot gate cannot see a single-glyph
typo, so a number that is not derived is a number that will eventually be wrong.

**Local props are named `tokenizer_*`, not `props`.** This directory goes on
`sys.path` as a flat namespace, and `props` is already taken by another video.
