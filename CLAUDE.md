Read `AGENTS.md`. It is the map for this repo and applies in full here.

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
