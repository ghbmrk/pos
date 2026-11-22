"""Root pytest guard: engine tests must run, never error.

Without a working LuaJIT (mainline build with `+=` support: tools/build_luajit.sh) dozens of engine
tests used to fail one by one as fixture errors and got waved through as "not a regression".
Now the whole session stops once, with the fix command. Use tools/test.sh, which builds it for you.
Escape hatch for pure-logic work only: POS_ALLOW_NO_LUAJIT=1 (the engine tests then error; never merge on that).
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _luajit_problem() -> str | None:
    from pos_engine.engine import _find_luajit
    from pos_engine import paths

    if not (paths.pob_src_dir() / "Launch.lua").exists():
        return "PoB submodule missing: run `git submodule update --init`."
    try:
        exe = _find_luajit()
    except FileNotFoundError:
        return "LuaJIT not found."
    probe = subprocess.run([exe, "-e", "local a=1 a+=1 assert(a==2)"], capture_output=True, text=True)
    if probe.returncode != 0:
        return f"LuaJIT at {exe} is too old (no `+=`): {probe.stderr.strip()}"
    return None


def pytest_sessionstart(session):
    if os.environ.get("POS_ALLOW_NO_LUAJIT") == "1":
        return
    problem = _luajit_problem()
    if problem:
        import pytest

        pytest.exit(
            f"ENGINE TESTS CANNOT RUN: {problem}\n"
            "Fix: run `tools/test.sh` (inits the submodule, builds LuaJIT once, runs the full suite).\n"
            "Do not merge with engine tests erroring: that is not 'not a regression'.",
            returncode=3,
        )
