# pos

Path of Sim. Durable project state lives in [STATE.md](STATE.md).

## Engine
`pos_engine/` drives Path of Building PoE2 headless (see [docs/engine-fork.md](docs/engine-fork.md)).
Setup: `git submodule update --init && tools/build_luajit.sh && pip install -r requirements.txt && python -m pytest pos_engine/tests`
