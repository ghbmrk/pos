# Prior art: PoE2 build tooling (S1)

Checked 2026-11-22 by cloning each repo and reading code; the X summary in the goal message was treated as unverified. "Verified" means checked in code or by running it here; "claimed" means README text only.

## Context that changes the plan

- **PoE2 1.0 launches 2026-12-11** (announced at gamescom 2026; e.g. [RPG Site](https://www.rpgsite.net/news/21188-path-of-exile-2-reaches-its-10-full-release-on-december-11)). Every tool below targets the 0.x data (passive tree `0_5`); all will need a data/engine update after launch. Design for a swappable, pinned PoB checkout from day one.
- Upstream Path of Building PoE2 is the only real calc engine. Everything credible drives it headless; anything else reimplements formulas and drifts.

## Projects

| Project | Exists | Licence | Last commit (total) | Calc engine | Container headless | Fit for parallel variants |
|---|---|---|---|---|---|---|
| [PathOfBuildingCommunity/PathOfBuilding-PoE2](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2) | yes | MIT | 2026-11-10 on `dev`; last release v0.23.1 2026-07-28 | is the engine (Lua) | **yes**: ships `src/HeadlessWrapper.lua` and a Dockerfile used for its test suite | base layer for everything |
| [MaxWilk/poe2-build-mcp](https://github.com/MaxWilk/poe2-build-mcp) | yes | MIT | 2026-06-23 (53 commits, all 2026-06-18..23) | upstream PoB driven via LuaJIT subprocess, JSON-RPC over stdio; pinned `a82a33b` + 1 patch | **yes, verified here** (see below) | best: already has a multi-process engine pool, `compare_to` A/B, optimizers |
| [HivemindOverlord/poe2-mcp](https://github.com/HivemindOverlord/poe2-mcp) | yes | MIT + "contribution restriction" clause (forking allowed) | 2026-10-25 (351 commits since 2025-11) | **own Python calculators** (`src/calculator/*`); optional TCP bridge into a running *desktop* PoB | no (bridge needs GUI PoB) | weak: numbers are a reimplementation, not PoB |
| [SFerenczy/poe2-agent](https://github.com/SFerenczy/poe2-agent) | yes | MIT | 2026-04-15 (99 commits) | upstream PoB Lua in-process via Rust `mlua` (vendored LuaJIT) | likely (claimed; not run) | Q&A agent tied to OpenAI Responses API; has a rate-limit-aware trade client |
| [deepwa7er/poe2-mcp](https://github.com/deepwa7er/poe2-mcp) | yes | **none** (all rights reserved) | 2026-06-20 (45 commits) | upstream PoB via `luajit` driver | likely (claimed; not run) | analysis only; code not reusable without a licence |
| [PartyPenguin/ExileOracle](https://github.com/PartyPenguin/ExileOracle) | yes | **none** | 2026-03-14 (5 commits) | none (no calcs) | n/a | stash/character access via a copied `POESESSID` browser cookie; not relevant to simulation |

Tool-count claims (64, ~38) match the READMEs; not counted independently.

### MaxWilk/poe2-build-mcp, run in this container

- Setup: `apt install luajit`, PoB-PoE2 checked out at the pinned commit with its patch, corpus downloaded from the project's release (sha256 matched the release manifest).
- Result: full test suite (`tests/`, 144 tests incl. engine, optimizers, corpus) passed with system LuaJIT 2.1 on Linux, no GUI.
- Throughput: engine boot 1.1 s; full reload-from-XML + recalc of the fixture build 0.24 s; 4 engine processes on 4 vCPUs gave 16.5 evaluations/s (near-linear). So ~1,000 variants per minute per 4 cores before any incremental-update optimisation. Measured on a small fixture build; large endgame builds will be slower (not measured).
- Snags found: `pyproject.toml` declares `mcp>=1.2` with no upper bound; a fresh install pulls mcp 2.x and the server fails to import (`mcp.server.fastmcp` removed). `uv.lock` pins 1.28.0, so `uv sync` works. The corpus build fetches from `repoe-fork.github.io`, which this cloud environment's network policy blocks; the release download from github.com works.
- Risk: single maintainer, built in one week, silent for 5 months; pinned PoB is 232 commits behind upstream `dev`. Its "self-update" only pulls the maintainer's own releases, so it updates for 1.0 only if the maintainer acts.

## Price data for gear tiers

| Source | Status | Covers | Terms / limits |
|---|---|---|---|
| [poe.ninja API](https://poe.ninja/docs/api) | supported public surface = **economy overview endpoints only**; PoE2 included | currency, uniques, other fixed-identity items; refreshes ~hourly for PoE2 | no numeric limit; "be reasonable", respect HTTP cache (~5 min, ETag), excessive use gets blocked; desktop apps should proxy via own backend with a contact UA; builds/character endpoints are internal, not for third parties |
| poe2scout.com API | third-party, used by MaxWilk and ExileOracle | currency + unique prices | terms not found; treat as best-effort |
| Official trade site (pathofexile.com/trade2) | **not a documented API**. [GGG developer docs](https://www.pathofexile.com/developer/docs) list only documented resources (incl. Currency Exchange); undocumented website APIs: "requests for access will be denied", reverse-engineering is against ToS 7i. No OAuth trade scope; new app registration currently closed | rare items with arbitrary mods | dynamic limits via `X-Rate-Limit-*` headers and `Retry-After`; commercial use of GGG IP not allowed |

Implication: **rare-item prices cannot be fetched at scale legitimately.** Uniques and currency can (poe.ninja). For rares, the price tier has to come from a model: e.g. cost per affix tier derived from crafting inputs (currency prices are available), calibrated by occasional manual trade samples. This is a design constraint, not a solved problem in any project above.

## Recommendation

Facts above; this section is judgement.

1. **Reuse the engine layer, build the orchestration.** Fork MaxWilk's engine pieces (`pob/pob_headless.lua`, `server/compute/engine.py`, `pob_code.py`, its tests) into this repo as a library under MIT, re-pinned to current PoB-PoE2. Build our own layer on top: build spec (from natural language), variant generator, parallel engine pool, price-tier model, result table. Expose it as MCP later if wanted.
2. Do not depend on MaxWilk's MCP server as-is: it is a single-build interactive session designed for chat, dormant since June, and its update path depends on one person before a 1.0 data change.
3. Do not use HivemindOverlord's calculators: they are not PoB.
4. Writing our own PoB wrapper from `HeadlessWrapper.lua` is the fallback if the fork proves tangled; cost is roughly the size of `pob_headless.lua` + `engine.py`, and MaxWilk's code shows the path.

Open questions for later tasks: how to model rare-item price tiers; whether the cloud environment should allow poe.ninja for live prices.
