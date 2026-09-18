# Writing a /lib component

## Before you write one

Check `lib/components/` first. The usual right answer is a new keyword argument
on an existing class, not a new class. Duplicated visuals are how a series stops
looking like a series.

## What belongs in /lib

A component earns its place when it is used by **two or more scenes**, or is
clearly needed by a future video in the same subject area. Until then it lives in
the video's `scenes/` directory next to the scene that uses it. When a second
scene reaches for it, that is the moment to promote it — move it, turn the
hardcoded bits into parameters, and add its tests.

Signals that something is a one-off: it encodes a specific sentence, a specific
narrative beat, or a layout that only makes sense beside one other element. The
`_callout` helpers in the tokenization scene are a worked example — braces over
a chip are plausibly reusable, but until a second scene needs them they stay
local.

## Shape of a component

- Subclass `VGroup`. Build children in `__init__` and expose them as named
  attributes (`self.box`, `self.rows`) so scenes can animate the parts.
- Everything visual comes from `lib/theme.py`; everything that moves gets its
  curve from `lib/motion.py`. No hex strings, no raw font sizes, no `self.play`
  without a `rate_func`.
- A node the viewer should recognise gets an icon (`lib.components.glyph`), not a
  labelled rectangle. "Running" is a glow (`lib.effects`), not a thicker border.
- Parametrize what a second video would want to vary: colour, size, counts,
  labels. Give defaults so the common case stays one line.
- Methods that change state (`highlight`, `activate`, `select`) return `self` so
  they compose with `.animate`.
- **Avoid attribute names Manim's `Mobject` already owns.** `dim` and `color` are
  taken and will fail at construction or silently misbehave — use `dimension`,
  `accent`, `deemphasise`. Both were real bugs caught by the tests here.
- `.animate` interpolates between two states of the *same* structure. A method
  that adds or replaces submobjects (like `ChatInput.clear`) cannot be animated;
  call it as a hard cut.

## Tests are part of "done"

Every component needs a structural test in `tests/test_components_structure.py`:
construction, the contract of its parameters, its invariants, and the `in_frame`
fixture if it has meaningful size. Assert behaviour, not implementation — "user
bubbles sit right of assistant bubbles", not "submobject 3 has x > 0".

Anything with meaningful layout also gets a snapshot case in
`tests/snapshot_cases.py`. Render it, look at it, and only then:

```bash
.venv/bin/python scripts/approve_baselines.py <case>
```

Approving a baseline you have not looked at defeats the entire tier.

## Determinism

Anything that looks random must be derived deterministically from its input — see
`vectors.stable_vector` and `tokens.fake_token_id`. Python's `hash()` is
randomized per process and will make snapshots flap. Never use it here.
