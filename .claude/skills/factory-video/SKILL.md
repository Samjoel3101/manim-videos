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
- **Watch the zoom budget** — see "Layout and the zoom budget" below. A set
  should compute its own pull-back factor and assert on it.
- **`marquee=` for the wide shot.** The in-bay title is a few pixels at full
  pull-back, so each station carries a second, larger name that is revealed only
  when the camera pulls out. `marquee_side` places it (`"left"` for a column),
  and it is clamped so neighbours cannot collide.
- **A `PipelineBox` title sits outside its frame**, not inside, so it cannot
  collide with whatever the enclosed stations put near their own top edge.
- **A tall box wears its name down the side** (`title_side="side"`), not across
  the top. A box fed from above has a rail coming down its midline, and a title
  sized for the pull-back is about as wide as the box, so a top title and the
  rail want the same space. Stopping the rail short of the words is the trap:
  the title is a wide-shot label and stays dark through every close-up, so all
  the viewer sees is an arrow ending in nothing. A column layout leaves its side
  margins empty and a tall box has height to spare — spend both.

## Typography

Never pass a point size. Type is specified as a **share of frame height** and
the point size is derived from the shot it will be read in:

```python
from lib import typography as typo

typo.text("heading", "Tokenizer", frame_width=SHOT_TIGHT)   # read in close-up
typo.text("title", "THE MODEL", frame_width=SHOT_WIDE)      # read at the pull-back
```

A set declares `SHOT_TIGHT` and `SHOT_WIDE` once, and every label states which
one it belongs to. That is the whole mechanism: absolute sizes are meaningless
in a video whose camera zooms, and the arbitrary `x2.6` multipliers that
preceded this are what "the typography looks odd" actually was.

Roles, largest to smallest: `display`, `title`, `heading`, `body`, `label`,
`caption`, `micro`. Reach for weight (`bold=True`) before another size step.
Nothing may fall below `typo.MIN_READABLE` (2% of frame height) at the shot it
is read in — `typo.audit()` checks a list of labels against that floor.

**Prefer one label sized for a shot between the two** over a small close-up
label plus a large one revealed at the end. Two labels in one bay was tried and
removed: they overlap, and the opacity dance that swaps them is exactly the kind
of thing the traps below punish. A single compromise size that clears the floor
at the pull-back and still fits the bay in close-up is simpler and cannot get
out of sync with itself.

A container whose header must share space with content needs a cap on the
header's share (`HEADER_SHARE` in `lib/components/factory.py`), or a title sized
for the wider shot leaves the slot with nothing.

## Layout and the zoom budget

The pull-back factor is `wide_frame_width / 14.22`, and it decides what is
possible. A set should compute it and assert on it at construction.

- A **wide** layout is width-bound at 16:9 and reaches ~2x.
- A **vertical column** is height-bound and lands nearer ~3x. That is the price
  of a top-to-bottom reading; it is affordable *only* because type is
  shot-relative. Fixed-size type at 3x is what made an early cut illegible.
- A tall column leaves the sides of a 16:9 frame empty. Spend that margin:
  `marquee_side="left"` puts station names in it, which both fills the frame and
  keeps the stack short.
- Wide short bays need `header_side="left"` — there is no vertical room for a
  stacked header, and the slot collapses to nothing if you try.

## Trails and routing

The complaint this section exists to prevent: *the trail goes through the boxes
instead of following the diagram.*

1. **Build the travel path from the rails**, never from node centres:
   `routing.join(rail_a, rail_b, ...)`. If the path is made of the drawn rails,
   it cannot disagree with them.
2. **Assert it.** A set's `validate()` should call
   `routing.assert_path_clears(...)` on anything that must go *around* things,
   so a routing regression fails at construction rather than in a render.
3. **Also assert the chords.** A comet is sampled once per frame and joined with
   straight segments, so a corner taken too fast cuts across things the path
   itself misses. `routing.assert_trail_clears(path, obstacles, steps=fps*run_time)`
   catches exactly that, and `path_clears` cannot.
4. **Place the dot on the path before attaching its trail.** A comet traces
   `get_center` from the frame it is added; a dot still sitting where it was
   draws one long chord across the whole set on its first frame. This produced a
   stray diagonal through the machines and looked exactly like a routing bug.
5. Keep `dissipating_time` short (~0.15s) on fast moves.
6. Rails are orthogonal. Use `routing.elbow()`; diagonals read as sloppy.
7. **A rail must land on the thing it feeds.** If something is in the way, move
   the obstacle, not the rail's endpoint. A gap of even half a unit reads as
   "these two are not connected", which is the opposite of what a diagram of a
   pipeline is for.

## Rows of anything: reserve the column, do not measure the text

A width argument on a label should reserve a **column**, not merely cap the
text. Laying a row out around its own label — `track.next_to(label, RIGHT)` —
puts every row's content wherever that row's word happened to end, so a chart
of "It" and "When" comes out with a ragged left edge. Build the row against a
fixed origin instead: label at x=0, content always at the same offset. Every
row's bounding box then starts at the same place, so a plain
`arrange(DOWN, aligned_edge=LEFT)` lines up all the columns at once.

Assert it. Alignment is invisible to the snapshot gate — a 16×16 luminance
signature cannot see a bar move a third of a unit — so a ragged edge ships
unless a structural test compares the left edges directly.

## Two traps that look like colour bugs

Both of these cost a long debugging session, and both present as "the text is
grey" rather than as what they are.

1. **Never call `set_opacity` on a glow halo.** A halo is a dozen *copies of the
   shape* with their fill cleared; `set_opacity` raises fill opacity too, so the
   copies become opaque plates that bury whatever the shape contains. Animate
   `set_stroke(opacity=...)` instead. Symptom: labels inside a glowing box look
   dim or vanish, while identical text outside the box renders bright — that
   contrast is the tell.
2. **Never animate a container `VGroup`'s geometry** (`station.animate.scale`).
   A VGroup carries its own rgba, transparent by default, and interpolating it
   drags every child's opacity down. Animate the shape (`station.bay`) or, as
   here, drop the pop and animate only the light.

When a label looks wrong, check whether the *same text outside the container*
renders correctly before suspecting the colour or the type system.

## Legibility beats accuracy in a silent cut

The tokenizer used to draw a leading space as `␣`, which is true to how tokens
work and read on screen as a broken glyph — "a half box in front of the word".
A notation that needs narration to land has nothing to explain it in a
thirty-second silent film. `display_token` now trims by default and takes
`show_space=True` for a shot that says out loud what the marker means. The
model keeps the real token either way; only the drawing changes. Same test for
any annotation: if a first-time viewer would read it as a rendering bug, it is
one.

## Motion blur: off

`harness.json` ships with motion blur **disabled on every profile**, and that is
a decision, not an oversight. A frame-blend pass smears the entire frame, so
during a camera move it reads as judder and slow motion rather than polish.
Clean motion here comes from easing and comet trails. The machinery is still
there for a specific shot that wants it; turn it on for one profile, render, and
look.

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
