#!/usr/bin/env bash
# Single entry point for the full suite. Run before every merge; engine tests must run, not error.
# Initialises the PoB submodule and builds LuaJIT if absent (cached in runtime/luajit/, keyed on the
# pinned ref in build_luajit.sh), then runs pytest. Extra args pass through to pytest.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -d third_party/PathOfBuilding-PoE2/src ]; then
  git submodule update --init
fi

want="$(sed -n 's/^REF=//p' tools/build_luajit.sh)"
have="$(cat runtime/luajit/.ref 2>/dev/null || true)"
if [ ! -x runtime/luajit/bin/luajit ] || [ "$want" != "$have" ]; then
  echo "test.sh: building LuaJIT (first run or pin changed)..." >&2
  bash tools/build_luajit.sh
fi

exec python -m pytest pos_repin pos_catalogue pos_pipeline pos_tiers pos_pool pos_engine/tests pos_mcp -q "$@"
