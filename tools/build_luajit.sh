#!/usr/bin/env bash
# Build the LuaJIT that PoB-PoE2 dev needs (compound assignment `+=`; distro luajit is too old).
# Pinned to the commit PoB-PoE2's own Dockerfile uses. Installs to runtime/luajit/.
set -euo pipefail
REF=2460b3ff93a1c955de3d62cfc825de7d68dc272e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
git clone -q https://github.com/LuaJIT/LuaJIT "$tmp/lj"
git -C "$tmp/lj" checkout -q "$REF"
make -C "$tmp/lj" -j"$(nproc)" >/dev/null
make -C "$tmp/lj" install PREFIX="$ROOT/runtime/luajit" >/dev/null
ln -sf "$(ls "$ROOT"/runtime/luajit/bin/luajit-* | head -1)" "$ROOT/runtime/luajit/bin/luajit" 2>/dev/null || true
echo "built: $("$ROOT/runtime/luajit/bin/luajit" -v)"
