# Session playbook

How a working session on this repo runs. Loaded on demand; `AGENTS.md` has the
short version.

## Two phases

**Setup** happens once per repo and once per video. Repo setup is done. Video
setup is `scripts/new_video.py`, which writes the per-video AGENTS.md, feature
list, progress log, scene manifest and render driver.

**Steady state** is every session after that: pick one unit of work, build it,
prove it, check it in. A session that does setup-scale work every time
re-decides architecture it already decided.

## The opening ritual

Before writing any code:

1. Confirm where you are — working directory and branch.
2. `./init.sh`. Idempotent; it fails loudly if the environment is unusable.
3. Read `claude-progress.txt` (repo root, then the video's) and the last few
   commits. Reconstruct state from the repo, not from being told.
4. Read the relevant `feature_list.json` and take the **highest-priority**
   incomplete item.
5. Run the Evaluator *before* starting. Do not take the previous session's word
   that its work still holds up.

Step 5 costs a couple of minutes and regularly saves an hour of building on a
broken assumption.

## One unit of work per session

A unit is one scene, or one component plus its tests — not "as much as fits".
End the session merge-ready: Evaluator green, no half-finished refactor, status
flipped in `feature_list.json`, an entry appended to `claude-progress.txt`.

Stopping one step early with a clean repo beats running out of context mid-way
with a broken one.

## Verifying before declaring done

A zero exit code from manim means the scene rendered. It does not mean the scene
is *right*. Before flipping a status to `passing`, render the scene and then
actually look at it:

```bash
ffmpeg -i out/<slug>/draft/videos/<module>/480p15/<SceneClass>.mp4 \
  -vf "select='not(mod(n\,40))',scale=427:240,tile=3x3" -frames:v 1 /tmp/grid.png
```

Open `/tmp/grid.png` and check every acceptance criterion in the feature list
against what you can see: overlaps, clipping, text running off frame, beats
firing in the wrong order. The structural tests cannot see any of that.

## Writing the progress entry

Plain narration, newest last. What you built, what you tried that did not work
and why, and what the next session should pick up. The failures are the valuable
part — they are what stops the next session repeating them.

## Pacing against the script

`script.md` gives each scene a duration budget that assumes narration over it.
Rendered scenes run shorter than budget until a voice-over pass locks the timing.
That gap is expected — do not pad scenes with empty waits to hit a number.
