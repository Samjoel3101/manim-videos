#!/usr/bin/env python
"""Record visual-regression baselines — the one way a baseline may change.

PROTECTED FILE (see AGENTS.md). Approving a baseline asserts "I looked at the
render and it is correct". Running this to silence a failing snapshot test
without looking is the exact reward-hacking move the harness exists to prevent.

Usage:
    .venv/bin/python scripts/approve_baselines.py            # list drifting cases
    .venv/bin/python scripts/approve_baselines.py NAME [...] # approve those cases
    .venv/bin/python scripts/approve_baselines.py --all      # approve everything
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.conftest import (  # noqa: E402
    BASELINE_DIR,
    TOLERANCE,
    drift,
    load_baseline,
    render_frame,
    signature,
)
from tests.snapshot_cases import CASES  # noqa: E402


def write_baseline(name: str, sig: list[float]) -> pathlib.Path:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    path = BASELINE_DIR / f"{name}.json"
    payload = {
        "name": name,
        "grid": 16,
        "note": "Downsampled luminance signature. Approve only after viewing the render.",
        "signature": [round(v, 6) for v in sig],
    }
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    return path


def main(argv: list[str]) -> int:
    names = sorted(CASES) if ("--all" in argv or not argv) else argv
    approve = bool(argv) and argv != ["--dry-run"]

    unknown = [n for n in names if n not in CASES]
    if unknown:
        print(f"unknown case(s): {', '.join(unknown)}")
        print(f"known: {', '.join(sorted(CASES))}")
        return 2

    for name in names:
        sig = signature(render_frame(CASES[name]))
        existing = load_baseline(name)
        if existing is None:
            status = "NEW"
        else:
            d = drift(existing, sig)
            status = "ok" if d <= TOLERANCE else f"DRIFT {d:.4f}"
        if approve:
            write_baseline(name, sig)
            print(f"approved {name:<20} ({status})")
        else:
            print(f"{name:<20} {status}")

    if not approve:
        print("\nnothing written — pass case names or --all to approve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
