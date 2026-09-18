---
name: factory-video
description: Build a continuous-shot "factory tour" explainer video in this repo — one uncut camera move through a persistent set of icon stations, with glow, eased motion and a final pull-back. Use when creating a new video, adding a beat or station to an existing one, restyling a scene, or when asked how this repo's videos are made. Covers the set/choreography split, the motion language, the icon and glow vocabulary, and the review loop that catches framing bugs the tests cannot.
---

# Factory-tour videos

The house format. One camera move, no cuts, through a set that is built once and
never torn down. The camera dives into each station in turn and pulls all the way
back at the end, so the final wide shot explains itself — the viewer recognises
the whole plant because they have already stood inside every part of it.

Read `AGENTS.md` first for the repo-wide rules (the `/lib` promotion rule, the
Evaluator, protected paths). This skill covers only how to build a video.

## The shape of a video

```
videos/<slug>/
  script.md          beat sheet with timecodes — write this FIRST
  scenes/<name>_set.py    where everything is
  scenes/scene_<name>.py  when the camera goes there
```

**Splitting the set from the choreography is not optional.** A 30-second uncut
take is ~70 animations whose timings all depend on each other. If the geometry is
interleaved with them, re-timing one beat means re-deriving positions, and nobody
does that twice.

The set module builds every mobject, positions it, and exposes stable anchors
(`entry`, `exit`, `slot_center`, rail endpoints) plus pre-built glow halos. The
scene module only plays animations against those anchors.

## Building the set

```python
from lib.components.factory import Station, PipelineBox, Conveyor
from lib.components.glyph import IconTile
from lib import effects, theme

self.server = IconTile("server", label="web server", color=theme.NETWORK)
self.tokenizer = Station("Tokenizer", subtitle="text → ids",
                         icon="binary", accent=theme.TOKEN, marquee="TOKENIZE")
```

Rules that come from real bugs:

- **Always give a station an icon.** A labelled rectangle says "a thing"; an icon
  says *which* thing before the viewer has read anything. `available_icons()`
  lists what is vendored; drop a new Lucide SVG into `lib/assets/icons/` to add
  one.
- **Pre-build glow halos in the set**, invisible, and let the choreography
  animate only their opacity. Constructing a halo mid-shot costs a beat.
- **Attach rails to the shape, not the group.** `IconTile.tile.get_left()`, not
  `IconTile.get_left()` — the group includes the caption and the anchor moves.
- **Keep the set under ~50 units wide.** The final pull-back is the total width
  ÷ 14.22; past ~3.5× the station marquees stop being readable.
- **`marquee=` for the wide shot.** The in-bay title is a few pixels at full
  pull-back. Marquees are clamped to bay width and sit below the bay so they
  cannot collide with each other or with a `PipelineBox` title.

## The motion language

Never pass a bare number or Manim's default easing. Everything comes from
`lib/motion.py`, so the whole back catalogue moves the same way:

```python
from lib import motion

self.play(..., run_time=0.7, rate_func=motion.MOVE)     # on-screen movement
self.play(..., run_time=0.3, rate_func=motion.ENTER)    # arriving
self.play(..., run_time=0.2, rate_func=motion.EXIT)     # leaving
self.play(..., run_time=0.5, rate_func=motion.FEATURE)  # the one emphatic move
self.play(motion.enter(chips), run_time=1.2)            # staggered group entrance
```

| Curve | Use for | Why |
|---|---|---|
| `ENTER` (decelerate) | anything arriving | enters at speed, settles — reads as landing |
| `EXIT` (accelerate) | anything leaving | starts still, accelerates away, shorter than the entrance |
| `MOVE` (standard) | on-screen A→B | the default; asymmetric, long decelerate |
| `SNAP` (sharp) | small nudges, dismissals | symmetric and quick |
| `FEATURE` (emphasized) | one move per beat, maximum | dramatic; stops being emphatic if overused |

Durations: `motion.duration_for(distance)` scales sub-linearly, so a hop and a
trip across the factory both feel right. Exits are shorter than entrances — the
viewer is already done with the thing.

## The visual vocabulary

- **Glow, not thicker borders**, for "this is running". `effects.glow()` returns
  a halo to place behind; `effects.Glowing` wraps the pair. Twelve layers costs
  the same as eight, and about a quarter of what an `ImageMobject` sprite costs,
  so do not be stingy.
- **Comet trails** on anything travelling (`effects.comet`). This is
  follow-through: it is what makes a packet read as having momentum rather than
  teleporting. Keep `dissipating_time` short (~0.15s) on fast moves — a long tail
  stops reading as a comet and starts reading as a line drawn through the set.
- **Motion blur is a render profile, not a scene concern.** `preview` and `final`
  apply an ffmpeg frame-blend pass automatically; `--no-blur` skips it.

## Camera

```python
from lib import camera

camera.snap_to(self, target, width=12.0)              # opening frame, no animation
self.play(camera.focus(self, station.bay, width=12.0, run_time=0.7), other_anim)
self.play(camera.frame_all(self, [set.everything], pad=1.0), run_time=1.4)
```

- **Play camera moves *with* the action at their destination**, never before it.
  That is why `focus` returns an animation instead of playing one. A camera that
  stops, waits, then lets something happen is what makes a shot feel cut-up.
- **Frame the shape, not the group** — `station.bay`, not `station`, or the
  invisible marquee hanging below drags the framing down.
- **A tight shot must clear its subject at 16:9.** Frame height is width ÷ 1.78.
  A 5.2-tall bay plus a caption needs width ≥ 12. This is the single commonest
  bug in this format and no test can see it.

## The build loop

1. Write `script.md` first: beat sheet, timecodes, duration budget. Pacing is a
   decision, not an outcome.
2. Build the set. Check its total extent and zoom factor before animating.
3. Build the choreography beat by beat, with the target timecode in a comment.
4. Render at the `test` profile and **look at the frames**:
   ```bash
   .venv/bin/python scripts/evaluate.py --video <slug> --scene <Class>
   ffmpeg -i out/<slug>/.../<Class>.mp4 \
     -vf "fps=1,scale=427:240,tile=5x6" -frames:v 1 /tmp/grid.png
   ```
   Then open `/tmp/grid.png`. Every framing bug found in this repo so far — bays
   cropped, titles hanging into close-ups, a vector escaping its bay, a comet
   drawing a hard line — was invisible to the test suite and obvious in the grid.
5. Only when the Evaluator is green and the frames are right, flip status in
   `feature_list.json` and append to `claude-progress.txt`.

## Adding a component

If a beat needs a visual that does not exist, check `lib/components/` first —
the answer is usually a keyword argument, not a new class. If it is genuinely
new and reusable (2+ scenes, or clearly needed by a future video), it goes in
`/lib` **with a structural test and, if it has layout, a snapshot case**. One-offs
stay in the video's `scenes/`. See `docs/component-guide.md`.

Watch for attribute names Manim's `Mobject` already owns — `dim` and `color` are
taken, and both have caused real bugs here.
