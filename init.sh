#!/usr/bin/env bash
# Idempotent environment bootstrap. Every session runs this BEFORE writing code.
# Safe to re-run; exits non-zero and loudly if the environment cannot be made usable.
set -euo pipefail
cd "$(dirname "$0")"

SYS_DEPS="libcairo2-dev libpango1.0-dev pkg-config ffmpeg python3-dev build-essential"

need_sys=0
pkg-config --exists pangocairo 2>/dev/null || need_sys=1
command -v ffmpeg >/dev/null 2>&1 || need_sys=1
if [ "$need_sys" = "1" ]; then
  echo "[init] installing system deps (cairo/pango/ffmpeg)…"
  if command -v apt-get >/dev/null 2>&1; then
    (apt-get update -qq && apt-get install -y $SYS_DEPS) >/dev/null 2>&1 \
      || sudo apt-get install -y $SYS_DEPS >/dev/null 2>&1 \
      || { echo "[init] FAILED to install: $SYS_DEPS"; exit 1; }
  else
    echo "[init] no apt-get; install manually: $SYS_DEPS"; exit 1
  fi
fi

if [ ! -x .venv/bin/python ]; then
  echo "[init] creating .venv…"
  python3 -m venv .venv
  # Debian-patched setuptools breaks sdist builds (srt); upgrade before installing.
  .venv/bin/pip install -q --upgrade pip setuptools wheel
fi

if ! .venv/bin/python -c "import manim" >/dev/null 2>&1; then
  echo "[init] installing python deps…"
  .venv/bin/pip install -q -r requirements.txt
fi

# Editable install so scenes can `from lib import ...` wherever manim is invoked
# from, instead of every scene file opening with a sys.path hack.
if ! .venv/bin/python -c "import lib" >/dev/null 2>&1; then
  echo "[init] installing the repo as an editable package…"
  .venv/bin/pip install -q -e .
fi

.venv/bin/python - <<'PY'
import manim, importlib.util, shutil, sys
assert shutil.which("ffmpeg"), "ffmpeg missing"
for m in ("pytest", "PIL", "numpy"):
    assert importlib.util.find_spec(m), f"{m} missing"
print(f"[init] OK  manim={manim.__version__}  python={sys.version.split()[0]}")
PY
