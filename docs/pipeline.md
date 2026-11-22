# Pipeline: build idea -> ranked variants per price tier (G1)

Status: decided. Design revised 2026-11-22 after advisor review (validation gaps, fixed config profile, tree-stage cost, task split). Builds on `docs/engine-fork.md` (engine), `docs/price-tiers.md` (tiers) and the code on `main` (`pos_engine/`, `pos_tiers/`, `data/tiers.yaml`).

## Principle

The LLM translates and explains; it never supplies a game fact or a number. Every name it emits must resolve to an entry in a catalogue exported from the pinned PoB data, and every number in a report comes from a PoB calculation or from `PriceModel` with its sample label. Anything that fails either check is rejected with suggestions, not repaired silently.

## Stages

```
 idea (text) or PoB code
        |  1. Spec      LLM (client side) + resolve/validate tools
        v
 BuildSpec (YAML, catalogue ids only, pinned to a PoB sha)
        |  2. Assemble  spec -> PoB build, round-trip checks
        v
 seed build (PoB XML) per variant axis combination
        |  3. Search    supports -> tree -> gear, inside tier budget
        v  4. Pool      N LuaJIT engine processes, cached
 evaluated candidates
        |  5. Report    rank per tier, deltas, limitations
        v
 report.md + results.sqlite
```

### 1. Spec (natural language -> BuildSpec)

A `BuildSpec` is a small YAML file. Two entry points produce the same schema:

- **From an idea**: the LLM fills the spec using only `resolve(kind, text)` lookups against the catalogue (kinds: class, ascendancy, skill gem, support gem, unique, base type, keystone, notable). Unresolved or ambiguous names return candidates; the LLM must pick one or ask.
- **From a PoB code** (import -> optimise, the stronger pattern per prior art): the code is decoded by the engine and converted to a spec; the idea text only adds axes and objectives.

```yaml
pob_sha: 601768b          # catalogue the ids belong to
class: Sorceress
ascendancy: Stormweaver
level: 90
main_skill: { gem: "Metadata/Items/Gems/SkillGemSpark" }
fixed:                    # what the idea insists on
  keystones: []
  uniques: []
axes:                     # what to compare; cartesian product = variant seeds
  ascendancy: [Stormweaver, Chronomancer]
  weapon_base: [staff, wand+focus]
tiers: [starter, budget, mid, high]
config_profile: pinnacle_boss  # fixed enemy/conditions profile, part of the cache key
objective: { maximise: auto, floors: { resist_capped: true, TotalEHP: tier_default } }  # auto = metric chosen per skill type
```

Validation is two-layer:

1. **Schema + catalogue**: every id exists in the catalogue for `pob_sha`; compatibility checks the catalogue can answer (support gem `requireSkillTypes` vs the skill's types, item base vs slot, ascendancy vs class).
2. **Engine round trip** (stage 2): the assembled build is loaded in PoB and checked for unrecognised gems, empty main skill, PoB's own warnings, and **unparsed mod lines**. The wrapper has no unparsed-mod check today: `eval_items` returns `false` only when an item fails to equip, and a line PoB cannot parse is kept with `extra` set (`Classes/Item.lua`) and contributes nothing. G3 adds that check, and gear search rejects any candidate with an unparsed line, otherwise such items score as silent zeros.

Limits of what is caught: `pos_engine`'s engine-limitation note is a hand-typed table with one entry (Mana Tempest), not a general detector of unmodelled mechanics. Reports say so, and new entries are added as they are found.

**Comparable numbers.** PoB results depend on configuration (enemy type and resistances, charges, conditions, buffs). Every spec names a fixed **config profile** (`data/config_profiles.yaml`, applied with `set_config`), and the profile is part of the cache key. The metric is chosen per skill type rather than always `TotalDPS`: the wrapper's own note says `TotalDPS` is one hit of the main skill and `FullDPS` an upper bound that may count hits that do not overlap on one target. G3 defines the mapping and the report names the metric used.

### 2. Assemble

Spec -> PoB XML via the existing engine calls (`new_build`, `set_class`, `set_level`, `add_skill_group`, `add_item`, `alloc_passive`). One seed build per axis combination. Seeds start with a minimal tree (class start + ascendancy) and placeholder gear at the tier's default allocation, so search starts from a legal build.

### 3. Search

Full combinatorial search is out of reach (supports x tree x 8 gear slots). The search is staged coordinate descent with a narrow beam, each stage holding the others fixed. Supports and tree are close to tier-independent, so they run **once per seed** at a mid-tier gear placeholder; only gear runs per tier. A second support pass runs on the best gear set per tier.

| Stage | Space | Method | Evals (estimate, unmeasured) |
|---|---|---|---|
| Supports | eligible supports for the main skill (catalogue filter) | single-swap deltas for all, then beam (width 5) over the top 12 up to the socket count | ~150 per seed, plus a short re-check per tier |
| Tree | passive points at the spec level | PoB-side `optimize_passives` greedy (already in the fork; `reset` re-plans from scratch), with keystones/notables from `axes` forced on | per seed: greedy with up to 50 what-if calcs per pick, so ~5,000 calcs at ~100 points; the dominant cost |
| Gear | per slot: affix groups x ranks from the `pos_tiers` resolver; uniques from the catalogue | per slot, synthesise ~20-40 candidate items that fit the slot's share of the tier budget; `eval_items` scores them in one engine call; then move budget points between slots (take from the slot with the lowest marginal gain per point, give to the highest) until no gain | ~600-900 per seed x tier |
| Re-check | top 5 per seed x tier | full reload + recalc, floors enforced | 5 |

Outside the search for now: jewels, runes/soul cores, and weapon-set passive points. They stay as in the seed (or empty) and the report says so.

Constraints enforced inside search, not after: tier point budget (`TierTable`), resistance cap and attribute requirements as floors, one unique per name, slot eligibility from mod tags.

Known weaknesses (judgement): coordinate descent finds local optima and is order-sensitive, so it can miss combinations whose value only appears together (for example a conversion unique plus matching supports). Mitigations: axes let the user force such combinations; the second pass re-runs supports after gear. A genetic or MCTS layer is deferred until reports show this matters.

### 4. Evaluation pool

- N persistent `PobEngine` processes (default: CPU count), each booted once (~1.1 s) and fed jobs `(seed_xml_hash, mutations) -> stats`.
- Results cached in SQLite keyed by `(pob_sha, canonical XML hash, stat keys)`; repeated candidates across tiers and passes are free.
- Measured so far: 16.5 evals/s on 4 vCPUs on a small fixture build, near-linear in processes (`docs/prior-art.md`). Large endgame builds are not measured; task G4 measures one before any further estimate is trusted.
- The tree stage can run inside one worker per seed while other workers take gear jobs.
- A crashed or hung worker is restarted and its job retried once; a job that fails twice is recorded as an engine failure in the report.

### 5. Report

Per tier: top variants ranked by the objective, with DPS, EHP, resistances, the gear and support list, the delta versus the tier's best, the `PriceModel` estimate with its "N samples, dated D" label, and every engine limitation note. Across tiers: which axis value wins at which budget (the main question the goal asks). Output: `report.md` plus `results.sqlite` for drill-down; the LLM may summarise but only quotes numbers from these files.

## Interface

Core is a Python library (`pos_pipeline`) with thin fronts over it:

- **CLI**: `pos spec validate`, `pos run spec.yaml --tiers ... --workers N`, `pos report`. Deterministic, scriptable, no LLM. Used by tests and for long runs.
- **MCP server**: tools `resolve`, `validate_spec`, `import_pob`, `run` (async, returns a run id), `run_status`, `get_report`, `compare`. This is the natural-language front: Claude Code or Claude Desktop is the LLM, so no API key or per-run billing is built in, and the client's own model choice applies.
- **No embedded LLM call** in the pipeline itself, under the recommended option below.

## Cost per run

Unverified estimates for one idea with 4 seeds (axis combinations) x 4 tiers:

| Item | Estimate | Basis |
|---|---|---|
| Tree calcs | 4 seeds x ~5,000 = ~20,000 | greedy `optimize_passives`, run once per seed |
| Support + gear evals | 4 x ~150 + 16 x ~900 = ~15,000 | search table above |
| Wall time, 4 cores | ~35 min at 16 evals/s, if a what-if tree calc costs about one eval; unknown on large builds | measured fixture rate only |
| Wall time, 16 cores | ~10 min | scaling measured to 4 processes only |
| LLM tokens (MCP client) | ~20-50k to write and validate the spec, ~10-20k to read the report | tool outputs are compact ids and tables; no build XML enters the context |
| Money | engine compute is local; LLM cost is the client's plan usage | no API calls from the pipeline |

These numbers are not trusted until G4 (pool benchmark on a large build) and G6 (tree-stage timing) measure them; both gate G8. The cost lever is the number of seeds, which multiplies the tree stage, then tiers, which multiply gear. The CLI prints the job count and estimated time before starting and refuses above a set cap unless forced.

## Data and the 1.0 update path

Everything game-specific comes from one place: the pinned PoB submodule. A catalogue export (`tools/export_catalogue.lua`, run by LuaJIT) writes `data/catalogue/<pob_sha>.json` from `Data/Gems.lua`, `Data/Skills/*`, `Data/Uniques/*`, `Data/Bases/*`, `Data/ModItem.lua` and the tree in `TreeData/<version>/`. Nothing game-specific is hand-typed except `data/tiers.yaml`.

Re-pin at 1.0 (expected 2026-12-11, once PoB publishes 1.0 data), scripted as `tools/repin.sh <sha>`:

1. Bump the submodule (and LuaJIT `REF` if PoB's Dockerfile changed); run `pytest pos_engine/tests`.
2. Export a new catalogue; diff it against the old one (renamed, removed, new gems/uniques/mods).
3. Re-validate every saved spec against the new catalogue; specs naming removed things fail with suggestions.
4. Re-resolve `tiers.yaml` ranks (automatic); flag new affix groups with no premium weight; mark price anchors stale (economy reset).
5. Golden end-to-end run on one fixture spec; review value shifts rather than updating goldens blindly.

Specs record `pob_sha`, so old results stay reproducible against their own pin.

## Decision

**How the natural-language step runs.** Decided 2026-11-22 by the owner: **A, MCP server + CLI, no embedded LLM** (cmsg_01RxGYnd78N9kMbbAJ5pWDhUAqzfwd83TbFbqwuWojhQ3V).

| | A. MCP + CLI (recommended) | B. CLI with embedded Claude API calls | C. Both |
|---|---|---|---|
| NL front | Claude Code / Desktop session | pipeline calls the API itself | both |
| Needs API key, per-token billing | no | yes | yes |
| Runs unattended (scheduled sweeps) | yes, via scheduled headless Claude Code | yes, on any machine with an API key | yes |
| Build cost | small | medium (prompting, retries, key handling) | largest |

Unattended idea-to-report runs work under A too: headless Claude Code on a schedule drives the MCP server. Decision boundary: whether runs must happen **on a machine with no Claude client** (for example a plain server or CI job calling the API with a key). If not, A is cheaper and simpler, and B can be added later behind the same library without rework.

Other choices made here without a card (technical, reversible): objective default (max the per-skill DPS metric with resist and EHP floors, under a fixed config profile, overridable per spec), coordinate-descent search, SQLite cache, catalogue from PoB only.

## Implementation tasks

Each sized to a brief under 20k tokens and a finish under 150k. Model: Sonnet unless noted.

| Id | Task | Depends on |
|---|---|---|
| G2 | Catalogue export from pinned PoB (gems, supports with skill types, uniques, bases, ascendancies, keystones/notables) + `resolve()` with fuzzy suggestions + tests | - |
| G4 | Engine pool: N persistent workers, job API, restart/retry, SQLite cache; benchmark one large endgame build and record evals/s | - |
| G3a | BuildSpec schema + validator (catalogue + compatibility) + config profiles + per-skill metric mapping | G2 |
| G3b | Assembler spec -> PoB XML, round-trip checks incl. unparsed-mod detection, PoB code -> spec import | G3a |
| G5 | Support search (single-swap deltas + beam); verify socket-count and support uniqueness rules against PoB | G3b, G4 |
| G6 | Tree stage: wrap `optimize_passives` with forced keystones/notables; measure calcs and time on a large build (gates G8) | G3b, G4 |
| G7 | Gear search, first 3 slots (weapon, body, amulet): candidate synthesis from `pos_tiers` ranks and uniques, unparsed-line rejection, budget reallocation, resist/attribute floors. Riskiest task | G3b, G4 |
| G7b | Gear search: remaining slots | G7 |
| G8a | Orchestrator (seeds x tiers, once-per-seed stages) + CLI (`pos run`, job-count/time preflight, cap) | G5, G6, G7b; G4 and G6 benchmarks |
| G8b | Report (report.md + results.sqlite, metric/profile/limitation labels) + golden end-to-end fixture | G8a |
| G9 | MCP server over the library + a short usage guide for Claude Code/Desktop (Opus reviews the tool descriptions) | G8b (resolve/validate tools can start after G3a) |
| G10 | `tools/repin.sh` + catalogue diff + spec revalidation; run at 1.0 | G2, G3a |

G2 and G4 can start in parallel now; neither depends on the interface decision.
