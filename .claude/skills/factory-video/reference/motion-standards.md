# Where the motion numbers come from

Background for `lib/motion.py`. Read this when changing a curve or a duration,
not before — the constants are already applied, and the point of writing them
down once is that scenes do not re-litigate them.

## The curves

These are the Material Design motion curves, implemented in `lib/motion.py` as
real cubic-Béziers rather than approximated with Manim's named rate functions,
so they match the published values exactly.

| Name | cubic-bezier | Role |
|---|---|---|
| `STANDARD` | (0.4, 0.0, 0.2, 1.0) | movement between two on-screen positions |
| `DECELERATE` | (0.0, 0.0, 0.2, 1.0) | entering the frame |
| `ACCELERATE` | (0.4, 0.0, 1.0, 1.0) | leaving the frame |
| `SHARP` | (0.4, 0.0, 0.6, 1.0) | quick moves that stay on screen |
| `EMPHASIZED` | (0.2, 0.0, 0.0, 1.0) | the one move per beat that draws the eye |

The asymmetry is the whole point. An entering element arrives at full velocity
and settles, because the viewer needs time to read it once it has landed. An
exiting element starts still and accelerates away, because once the decision to
remove it is made, the viewer has stopped caring.

## The durations

Standard UI-motion guidance converges on 200–500ms for most transitions, with
entering at 200–300ms and exiting at 150–200ms — exits are consistently faster
than entrances. `lib/motion.py` encodes that as `D_SHORT`/`D_MEDIUM`/`D_LONG`
plus `EXIT_FACTOR`.

Duration also scales with distance: one duration for every move makes short hops
feel sluggish and long ones feel rushed. `duration_for()` uses a square-root
relationship, not a linear one, so crossing the whole factory does not take four
times as long as crossing one station.

**Explainer video is not UI.** These are floors, not targets. A beat the viewer
has to *read* is held longer than a button that just has to feel responsive. Use
`theme.T_*` for narrative holds and `motion.D_*` for the movement inside them.

## The animation principles that actually apply

Of the classic twelve, four do most of the work in diagram-style motion graphics:

- **Easing (slow in / slow out)** — covered above. Linear motion is the single
  clearest tell of an amateur animation.
- **Timing** — how long, and the pause either side. Usually the fix when a beat
  "feels wrong" but nothing is visibly incorrect.
- **Follow-through and overlap** — parts keep moving after the main body stops.
  In this repo that is `effects.comet`: the trail is what makes a travelling
  packet read as having momentum.
- **Anticipation** — a small wind-up before the main action. `effects.pulse` is
  built for this. It is a wind-up, so it goes *before* the event; using it after
  reads as a reaction and is the commonest way to misuse it.

**Stagger and lag** is the group-level version: lead the eye by animating the
most important element first and letting the rest follow. `motion.enter()` does
this with a default lag ratio of 0.15 — enough to read as a sequence, small
enough that the group still arrives as one gesture. A group appearing on a single
frame reads as a static slide.

## Sources

- Material Design — duration and easing (m3.material.io, m1.material.io)
- Nielsen Norman Group — *Executing UX Animations: Duration and Motion
  Characteristics*
- The 12 principles of animation (Thomas & Johnston), as applied to motion
  graphics

## What is not achievable in Manim

Recorded here so nobody re-derives it:

- **No gaussian blur.** Glow is faked with concentric strokes, which works well.
  A true soft drop shadow behind a filled card is not available — that would be
  an ffmpeg post-process.
- **No motion blur.** Handled as an ffmpeg `tmix` frame-blend pass in
  `render.py`, applied on the `preview` and `final` profiles.
- Measured on this repo at 1080p60: a 12-layer stroke glow renders in ~1.4s per
  animation-second; the equivalent pre-blurred `ImageMobject` sprite takes ~5.6s.
  Layer count barely affects cost. Cairo's alpha compositing is the bottleneck,
  not path count.
