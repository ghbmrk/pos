# Engine fork (S2): result is "stay on fork"

Checked 2026-11-22 by running it. Engine layer forked from [MaxWilk/poe2-build-mcp](https://github.com/MaxWilk/poe2-build-mcp) at `2414ef8` (MIT; licence kept in `LICENSE.maxwilk-poe2-build-mcp`) and re-pinned from PoB-PoE2 `a82a33b` (2026-06-13) to `dev` `601768b` (2026-11-10), 232+ commits.

## Layout
- `pos_engine/pob_headless.lua`, `engine.py`, `pob_code.py`, `skilltext.py`: forked verbatim except imports and `paths.py` (new, 25 lines).
- `third_party/PathOfBuilding-PoE2`: git submodule, pinned. **Zero patches to PoB.**
- `tools/build_luajit.sh`: builds LuaJIT into `runtime/luajit` (gitignored).
- `pos_engine/tests/`: engine-only subset of the fork's tests, 63 tests.

## Findings
1. **New requirement: LuaJIT built from mainline.** PoB-PoE2 dev now uses `+=` (first in `Modules/Main.lua`, commit `249406214`, 2026-08-28). Distro LuaJIT (Ubuntu 24.04, 2.1.0-git2023) fails with `'=' expected near '+'`. PoB's own Dockerfile pins LuaJIT `2460b3ff`, which supports it; `tools/build_luajit.sh` uses the same pin. Builds in about 30 s.
2. **Result: 63 of 63 engine-layer tests pass** on PoB dev (about 106 s), including the Fireball golden DPS (124.833) and import-code fixture. Without any fix attempts.
3. **Split Personality patch dropped.** The fork's one PoB patch still applies cleanly, but the multi-class-start test passes without it on current dev, so no patch is carried.
4. Not run: the fork's 18 corpus/optimizer tests (they need `corpus.sqlite`, which comes from `repoe-fork.github.io` or a release asset; both blocked here). They exercise code outside the forked engine layer.
5. Dropped from the fork on purpose: MCP server, corpus, optimizers, solver.

## Next re-pin (PoE2 1.0, 2026-12-11)
`git -C third_party/PathOfBuilding-PoE2 fetch && git checkout <sha>`, rerun `pytest pos_engine/tests`. Expect new LuaJIT syntax needs again; bump `REF` in `tools/build_luajit.sh` to PoB's Dockerfile pin when it changes. Golden values (Fireball) may legitimately shift with 1.0 balance changes; review rather than blindly update.
