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
| `run_status`, `cancel_run` | Lifecycle (every job kind). State is derived from files in the run directory, so it survives a server restart. |
| `get_report(run_id)` | The deterministic `report.md` (also `results.sqlite`, `run.json` paths). |
| `compare(run_a, run_b)` | Best result per tier in two runs, with the delta. |
| `list_runs` | Recent background jobs with their kind (run, sweep, slate). |

### Ideation (I6, design in docs/ideation.md)

| Tool / prompt | Purpose |
|---|---|
| prompt `ideate(idea, constraints?)` | The ideation procedure as an MCP prompt (in Claude Code: `/mcp__path-of-sim__ideate`). Text in `pos_mcp/ideate.py`; benchmark ids, tiers, slots and thresholds are filled from data files at call time. |
| `ideation_guide(idea, constraints?)` | Same text as a tool, because clients do not invoke prompts on their own; the server instructions tell the client to call it for goal-style requests. |
| `meta_lessons` | Compounding patterns from past metas as priors (docs/meta-lessons.md); ids go in `archetype.patterns`. |
| `search`, `bridges`, `enablers`, `explain` | Catalogue queries (docs/catalogue-queries.md), compact results; `explain` resolves by exact name and returns the quotable `text` lines (newest unique variant only). |
| `sweep(spec, kind, searched=true)` | Background job (`python -m pos_mcp.jobs sweep`): probe seed = first variant, supports- and tree-searched (cap 200) unless `searched=false`; metric under the first boss benchmark's options; writes `sweep.json` and `report.md`. Spark L90 keystone, 2 workers: 100 s. Default workers = half the CPUs (4 workers on 4 vCPU / 16 GB was OOM-killed). |
| `play` (+ prompt `play`) | L6 end-to-end loop as one background job: screen the slate's ideas, sim-verified creative rounds, inner loop on finalists, player report (docs/play.md). Poll `run_status`, then `get_report`. |
| `validate_slate`, `preflight_slate`, `run_slate` | Slate gate (docs/slate.md), estimate, and the slate runner as a background job (`slate run`, report `slate_report.md`; docs/slate-run.md). |

`run_status`, `cancel_run`, `get_report` and `list_runs` cover every job kind; one job runs at a time. The job's report file is recorded in `meta.json`.

**Prompt rules** (what the text steers; the gate enforces the checkable ones): names only from the catalogue, PoE1 memory treated as a guess; every claim cites a verbatim PoE2 quote from `explain`; no numbers outside reports; damage-dealing main skills only; 1-3 key pieces fixed in the spec; 6-10 candidates that differ in kind (delivery, damage, defence, class) with at least one non-obvious idea and one built on a sweep lead when a sweep ran; per-candidate weapon bases; report ranks on benchmarks only and reads ablation verdicts plainly.

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

Ideation: *"/mcp__path-of-sim__ideate a tanky lightning build that kills Arbiter on a budget"*, or ask the same in plain words. Expected flow: catalogue queries, a slate of 6-10 archetypes, `validate_slate` (fix rounds), a summary table, `preflight_slate` (a 6-candidate dry-run slate estimated 14 min on 4 vCPU), `run_slate`, `get_report`.

Unattended: headless Claude Code on a schedule drives the same server (`claude -p "..."` with the server configured).

## Limits

- Specs and tool text depend on the pinned PoB data; after a re-pin (`tools/repin.sh`) names are re-resolved by the catalogue, and old saved specs are revalidated by that script.
- Benchmark numbers marked unsourced (B3, waits for 1.0 data) come back as incomplete flags, not guesses; price anchors are still empty (see docs/price-tiers.md).
- One background job at a time; cancel kills the whole process group.
- The prompt's quality depends on the client model; I7 measures it on fixed prompts.
