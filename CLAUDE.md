Read `AGENTS.md`. It is the map for this repo and applies in full here.

**"How a change is made" in `AGENTS.md` is mandatory and applies to every change
in this repo.** Plan in detail → size the change → build or delegate → review →
verify the headline claims yourself. Answering a question or investigating
something read-only is not a change and does not need the loop.

**Plan every time; delegate when the change is large.** One or two files, no new
module, no new test, provable by a gate run — build it yourself. A feature, a
new component, several files, anything needing a render and a frame review to
prove, anything with parts that land in order — hand the plan to a subagent. On
the boundary, delegate. Size it *in* the plan, not before writing one.

Claude-Code mechanics for that loop:

- Use the `Agent` tool (`general-purpose`) for both the implementer and the
  reviewer. Run them in the background so the user can interject; a long
  implementation run here is tens of minutes.
- Write the plan to a file in the scratchpad and give the subagent its path,
  rather than pasting the whole plan into the prompt. The reviewer gets the same
  path, so both are working from one text.
- Tell the implementer to commit and push to the session's designated branch,
  and tell the reviewer explicitly **not** to modify, commit, or push anything.
- Give the reviewer the implementer's specific claims and ask it to check them.
  "Verify this list" produces a sharper review than "look this over".
- This loop is instruction, not enforcement — there is no hook behind it,
  because `.claude/hooks/` is a protected path. Follow it anyway.

Claude-Code-specific notes only:

- A PreToolUse hook (`.claude/hooks/guard_protected_paths.py`, registered in
  `.claude/settings.json`) blocks writes to the paths that grade your work. A
  denial from it is not a bug to work around — see "Protected paths" in AGENTS.md.
- That hook also inspects Bash commands. It currently matches any command that
  both mentions a protected path and contains a redirect, so a heredoc that
  *documents* the Evaluator gets blocked. Use the Write tool for those files
  rather than trying to defeat the guard.
- Rendering is slow. Use `--skip render` on the Evaluator for the inner loop,
  and the full gate set before you call anything done.
- Reviewing a render means actually looking at it: extract frames with `ffmpeg`
  and read the resulting image, rather than inferring from a zero exit code.
