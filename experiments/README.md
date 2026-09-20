# experiments/

Throwaway spikes. **Nothing in here is shipped, tested, or wired into the
Evaluator**, and nothing in `lib/`, `videos/`, `tests/` or `assets/` imports it.
Each spike answers one question and then either graduates into a real proposal
or gets deleted.

There is no live spike right now.

## Graduated

### slides_lifecycle — click-to-advance presentation → `lib/slides.py`

**Question asked:** is a click-driven deck good enough to present this material,
compared with the continuous uncut take the repo ships?

**Answer: yes, and it is now a repo convention.** The spike's 474-line
`slides_scene.py` was welded to one film. It has been split:

- the generic half — the arrival/clear-down classification, `no_stops()`, the
  `play` split state machine — is `lib/slides.py` (`ClickDeck`);
- the lifecycle-specific half — the looping animation, the decode-ramp
  suppression, the expected counts — is
  `videos/chatgpt_request_lifecycle/slides.py`, 102 lines, most of them the
  comments that record what the frames taught;
- a second film, `videos/chatgpt_message_journey/slides.py`, converts in 66
  lines (about 25 of code), which is the check that the machinery is generic
  rather than moved;
- `scripts/build_slides.py <slug>` replaces the spike's `build.py`;
- `tests/test_slides_convention.py` enforces the convention inside the existing
  `unit` gate — no gate name was added, because `gate_unit` already runs
  `pytest tests/` over the whole directory;
- `docs/slides.md` carries everything the spike's write-up here used to: the
  four load-bearing behaviours, the per-repeat calls with their reasons, the
  authoring rules, the build commands and the Reveal.js offline-cache note.

The deck still produces **97 animations, 70 stops** for the lifecycle film,
chunks 0.20s–2.67s, median 0.83s, none a single frame — identical to the spike,
which is how the promotion was checked.

`manim-slides` is no longer a spike-only dependency; it is what
`videos/<slug>/slides.py` imports.

**Read `docs/slides.md`, not this file.** This entry exists so the graduation is
recorded rather than implied.
