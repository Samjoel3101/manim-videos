#!/usr/bin/env python3
"""PreToolUse hook: refuse writes to the files that grade the agent's work.

Harness-engineering pillar 9 / anti-pattern "an agent editing both the work and
its own evaluation". An agent that can rewrite the Evaluator, the test fixtures
or the approved baselines can make a broken component "pass" by weakening the
check. Those paths are enforced mechanically here rather than asked for politely
in a doc, because a doc is a rule the next session may not read.

Deliberately NOT protected: tests/test_*.py and tests/snapshot_cases.py. The
generator is *required* to add a test for every new /lib component, so it must
be able to write new test files. Deleting or gutting an existing one still shows
up in review, and CI runs the suite from the base branch's fixtures.

Reads a PreToolUse payload on stdin, exits 0 to allow. On a violation it emits
the deny decision on stdout and exits 0 (the documented hook contract).
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

with open(ROOT / "harness.json") as fh:
    PROTECTED = json.load(fh)["protected_paths"]

# Bash commands that could clobber a protected path without going through Edit.
REDIRECT_OR_DELETE = re.compile(r"(>>?|\brm\b|\bmv\b|\bcp\b|\btruncate\b|\bsed\b\s+-i)")


def _is_protected(raw_path: str) -> str | None:
    """Return the matching protected rule, or None."""
    if not raw_path:
        return None
    try:
        rel = pathlib.Path(raw_path).resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        rel = raw_path.lstrip("./")
    for rule in PROTECTED:
        if rule.endswith("/"):
            if rel.startswith(rule):
                return rule
        elif rel == rule:
            return rule
    return None


def _deny(rule: str, detail: str) -> None:
    reason = (
        f"Blocked: '{detail}' is a protected harness path (rule: {rule}).\n"
        "This is the evaluation side of the harness — the Evaluator, its test "
        "fixtures, the approved visual baselines, this hook, and CI. Changing "
        "them to make your own work pass is the failure mode the harness exists "
        "to prevent.\n"
        "If the check itself is genuinely wrong, say so in claude-progress.txt "
        "and raise it with a human instead of editing it.\n"
        "To re-record a baseline after LOOKING at the render, run:\n"
        "  .venv/bin/python scripts/approve_baselines.py <case>"
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # never block on a malformed payload

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    if tool in ("Write", "Edit", "NotebookEdit"):
        target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        rule = _is_protected(target)
        if rule:
            _deny(rule, target)

    elif tool == "Bash":
        command = tool_input.get("command", "")
        if REDIRECT_OR_DELETE.search(command):
            for rule in PROTECTED:
                token = rule.rstrip("/")
                if token and token in command:
                    _deny(rule, token)

    sys.exit(0)


if __name__ == "__main__":
    main()
