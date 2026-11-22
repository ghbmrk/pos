# MCP server (G9)

`pos_mcp/` exposes the pipeline to Claude Code or Claude Desktop. The client's own model is the natural-language front, so there is **no API key and no LLM call inside the pipeline** (decision cmsg_01RxGYnd78N9kMbbAJ5pWDhUAqzfwd83TbFbqwuWojhQ3V). The CLI (`python -m pos_pipeline ...`) stays the scriptable, deterministic front.

## Tools

| Tool | Purpose |
|---|---|
| `resolve(kind, names)` | Name -> catalogue entry. `exact`, `ambiguous` or `unresolved` + suggestions; never guesses. Kinds: class, ascendancy, skill, support, unique, base, keystone, notable. |
| `validate_spec(spec)` | Spec (YAML text or object, docs/spec.md) against catalogue and known engine limits. |
| `import_pob(code)` | PoB share code -> draft spec + dropped-content warnings. |
| `preflight(spec, bases)` | Time estimate and cap check; no run. |
| `run(spec, bases, ...)` | Validates, applies the 45-minute cap (`force` overrides), starts a background process, returns `run_id`. One run at a time. |
| `run_status`, `cancel_run`, `list_runs` | Lifecycle. State is derived from files in the run directory, so it survives a server restart. |
| `get_report(run_id)` | The deterministic `report.md` (also `results.sqlite`, `run.json` paths). |
| `compare(run_a, run_b)` | Best result per tier in two runs, with the delta. |

**Grounding rule.** Game names reach a run only through the catalogue: `run` re-validates and refuses specs with unresolved names, and the server instructions tell the client to `resolve` before writing any name. The client is told to quote numbers only from the report. Both are enforced by the tools (validation) and by instruction (quoting); the second is not mechanically checkable.

Runs live in `runs/<id>/` (override with `POS_RUNS_DIR`): `spec.yaml`, `log.txt`, `run.json`, `report.md`, `results.sqlite`, `cache.sqlite`.

## Setup

Prerequisites (same as the engine tests): `git submodule update --init`, `bash tools/build_luajit.sh` (the distro LuaJIT is too old), `pip install -r requirements.txt` (includes `mcp>=2`; the server uses the v2 `MCPServer` API).

**Claude Code** (from the repo root):

```
claude mcp add path-of-sim -- python -m pos_mcp
```

or a project `.mcp.json`:

```json
{"mcpServers": {"path-of-sim": {"command": "python", "args": ["-m", "pos_mcp"]}}}
```

**Claude Desktop** (`claude_desktop_config.json`; use absolute paths):

```json
{"mcpServers": {"path-of-sim": {"command": "/abs/path/to/python", "args": ["-m", "pos_mcp"], "cwd": "/abs/path/to/pos"}}}
```

If the client ignores `cwd`, use `"args": ["-m", "pos_mcp"]` with `"env": {"PYTHONPATH": "/abs/path/to/pos"}`.

## Trying it

Ask: *"Test a Stormweaver Spark build at level 90. Use an Acrid Wand and a Lapis Amulet, mid tier, and benchmark it against Arbiter of Ash and Breach."* Expected flow: `resolve` for each name, `validate_spec`, `preflight` (the golden spec on 4 vCPU measured 143 s), `run`, a few `run_status` polls, `get_report`.

Unattended: headless Claude Code on a schedule drives the same server (`claude -p "..."` with the server configured).

## Limits

- Specs and tool text depend on the pinned PoB data; after a re-pin (`tools/repin.sh`) names are re-resolved by the catalogue, and old saved specs are revalidated by that script.
- Benchmark numbers marked unsourced (B3, waits for 1.0 data) come back as incomplete flags, not guesses; price anchors are still empty (see docs/price-tiers.md).
- One run at a time; cancel kills the whole process group.
