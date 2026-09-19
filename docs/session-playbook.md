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

## Plan, delegate, review

`AGENTS.md` states the rule; this is the protocol. It is mandatory for every
change to this repo — scenes, components, tests, docs, manifests, config.
Answering a question, or read-only investigation that changes nothing, is not a
change and does not need the loop.

The reason is the one already written into the Generator/Evaluator split, one
step further out: an agent that decides what to build, builds it, and then
judges its own build has no independent check at any of the three points. Every
defect this repo has shipped was invisible to the five gates and caught by a
fresh pair of eyes — rails that had never been drawn, a bar chart with no
number on it, a label three times under the readability floor.

### 1. Plan

Before any file is written, read the code and work out the whole change. A plan
that is worth handing over states:

- what is wrong or missing, precisely, with `file:line` where it applies;
- the exact files, symbols and constants involved;
- the measured numbers it depends on — geometry, extents, timings — **measured,
  not assumed.** Plans written from memory produce implementations that fail on
  first render;
- the step-by-step or beat-by-beat shape of the result, with timings;
- the tests and baselines it needs;
- the verification that would prove it correct, in enough detail to execute;
- a definition of done, as a checklist;
- the hard rules that apply (theme, typography, motion, protected paths).

Write it to a file. The implementer and the reviewer then read the same text
instead of two paraphrases of it.

### 2. Delegate

Hand the plan's path to a subagent. Give it the repo rules, the exact commands,
the branch to commit and push to, and an explicit instruction to report what it
could not do. Ask for evidence rather than assurances: for anything visual, what
it *saw in a frame*, not what the code now says.

Expect it to depart from the plan. A plan written without rendering anything is
frequently wrong about sizes and timings; a good implementer measures, finds the
plan's error, and says so. Ask for those departures with reasons.

### 3. Review

A second subagent, which did not write the code. Give it the implementer's
specific claims and ask it to check them — "verify this list" produces a sharper
review than "look this over". Tell it to rank findings by severity, to separate
real defects from weaknesses, to name what is genuinely good, and to say plainly
if it finds nothing serious rather than manufacturing findings. Tell it not to
modify, commit or push anything.

### 4. Verify yourself

Before reporting to the user, check the headline claims with your own tools. Run
the Evaluator. Read the frames. A subagent's report is a claim, not a fact, and
the claims that matter most are the ones easiest to assert without checking.

### Fixing what the review finds

Small, precise fixes can go straight to an implementer with the findings
attached. Anything larger goes back through the loop from step 1.

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
