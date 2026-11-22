# pos

Path of Sim. Durable project state lives in [STATE.md](STATE.md).

## Engine
`pos_engine/` drives Path of Building PoE2 headless (see [docs/engine-fork.md](docs/engine-fork.md)).
Setup: `pip install -r requirements.txt && tools/test.sh`

`tools/test.sh` is the one test entry point: it inits the PoB submodule, builds LuaJIT once (cached in `runtime/luajit/`, rebuilt when the pin changes), then runs the full suite. Run it before every merge; engine tests must run. If LuaJIT is missing or too old, plain `pytest` stops at once with `ENGINE TESTS CANNOT RUN` and the fix, instead of dozens of fixture errors (`POS_ALLOW_NO_LUAJIT=1` skips the guard for pure-logic work only).
