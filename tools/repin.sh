#!/usr/bin/env bash
# Re-pin PoB-PoE2 to a new commit and report what moved (docs/repin.md).
#   tools/repin.sh <pob_sha> [--skip-tests] [--specs DIR]
# Steps: bump submodule; bump LuaJIT REF if PoB's Dockerfile pin changed (and rebuild); pytest pos_engine/tests;
# export the new catalogue (old one is kept); write docs/repin/<new7>.md (catalogue diff, spec revalidation, tier checks).
# Exit status: 0 clean; 1 engine tests failed or a saved spec fails; 2 usage/setup error. Nothing is committed.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SUB="$ROOT/third_party/PathOfBuilding-PoE2"
sha="${1:-}"; shift || true
skip_tests=0; specs="$ROOT/specs"
while [ $# -gt 0 ]; do
  case "$1" in
    --skip-tests) skip_tests=1 ;;
    --specs) specs="$2"; shift ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac; shift
done
[ -n "$sha" ] || { echo "usage: tools/repin.sh <pob_sha> [--skip-tests] [--specs DIR]" >&2; exit 2; }
cd "$ROOT"
[ -e "$SUB/.git" ] || { echo "submodule missing: git submodule update --init" >&2; exit 2; }
[ -z "$(git -C "$SUB" status --porcelain)" ] || { echo "submodule has local changes; refusing (zero-patch policy)" >&2; exit 2; }

old="$(git -C "$SUB" rev-parse HEAD)"
old_cat="$ROOT/data/catalogue/${old:0:7}.json"
[ -f "$old_cat" ] || { echo "no catalogue for current pin: $old_cat" >&2; exit 2; }

echo "== 1. bump submodule ${old:0:7} -> $sha"
git -C "$SUB" fetch -q origin "$sha" 2>/dev/null || git -C "$SUB" fetch -q origin || { echo "fetch failed" >&2; exit 2; }
git -C "$SUB" checkout -q "$sha" || { echo "checkout $sha failed" >&2; exit 2; }
new="$(git -C "$SUB" rev-parse HEAD)"
[ "$new" != "$old" ] || { echo "already pinned to $new" >&2; exit 2; }

want="$(grep -E 'git checkout [0-9a-f]{40}' "$SUB/Dockerfile" 2>/dev/null | grep -i luajit | grep -oE '[0-9a-f]{40}' | head -1)"
have="$(grep -E '^REF=' tools/build_luajit.sh | cut -d= -f2)"
if [ -n "$want" ] && [ "$want" != "$have" ]; then
  echo "   LuaJIT pin changed ${have:0:7} -> ${want:0:7}; updating tools/build_luajit.sh"
  sed -i "s/^REF=.*/REF=$want/" tools/build_luajit.sh
  rm -rf runtime/luajit
fi
[ -x runtime/luajit/bin/luajit ] || bash tools/build_luajit.sh || { echo "LuaJIT build failed" >&2; exit 2; }

status=0
if [ "$skip_tests" = 0 ]; then
  echo "== 2. pytest pos_engine/tests"
  python -m pytest pos_engine/tests -q || status=1
fi

echo "== 3. export catalogue"
python -m pos_catalogue export || { echo "catalogue export failed" >&2; exit 1; }
new_cat="$ROOT/data/catalogue/${new:0:7}.json"

echo "== 4. diff, spec revalidation, tier checks"
python -m pos_repin report --old "$old_cat" --new "$new_cat" --specs "$specs" || status=1

[ "$status" = 0 ] && echo "re-pin OK" || echo "re-pin needs attention: see docs/repin/${new:0:7}.md and test output"
echo "next: review the report, fix specs, update pin constants in tests, commit (old catalogue is kept for reproducibility)"
exit "$status"
