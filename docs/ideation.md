# Creative ideation from high-level prompts (I1)

Status: design, 2026-11-22; built through I6 (MCP prompt and tools, docs/mcp.md). Owner requirement (cmsg_01RxGYnd78N9kMbbAJ5pWDhU6o4n9NQafMk2fcJq7WYpEm): from a high-level prompt ("a tanky lightning build that deletes Arbiter on a budget"), the system proposes **divergent** candidate builds, distinct archetypes, not only an optimised version of one build the user already named. Works inside the decided interface: MCP server + CLI, no embedded LLM (cmsg_01RxGYnd78N9kMbbAJ5pWDhUAqzfwd83TbFbqwuWojhQ3V, `docs/pipeline.md`).

## Principle

Divergence comes from two generators, and neither is trusted on its own:

1. **The client LLM** proposes archetypes. It is good at analogy and cross-domain combination, and bad at knowing which PoE version a mechanic belongs to and at numbers.
2. **The engine** proposes interactions by brute marginal sweeps (every keystone, every unique per slot, every support) on a seed build. It is blind to anything PoB does not model, but it cannot hallucinate.

Every candidate, from either generator, passes the same gates as any spec (`docs/pipeline.md` principle): names resolve in the pinned catalogue, numbers come from the engine. Ideation adds three gates: a **mechanism citation** gate (the claimed interaction must quote PoE2 catalogue text), a **diversity** gate (the slate must span distinct archetypes), and an **ablation** gate (the claimed key piece must actually move the benchmark number).

## Does MCP-only block this? No

Checked against each need:

| Need | Under MCP + CLI | Blocked? |
|---|---|---|
| Divergent generation | Client model generates; server ships an MCP **prompt** (`ideate`) that fixes the procedure and output shape | no |
| Enforcing diversity and grounding | Server-side deterministic validators (`validate_slate`), not prompt wording | no |
| Interaction discovery | Read-only catalogue queries + engine sweeps are plain tools | no |
| Unattended runs | Scheduled headless Claude Code calls the same tools (already decided) | no |
| Control of sampling (temperature, n samples) | Not available to the server | minor: diversity is enforced by the validator instead, and the prompt asks for more candidates than are kept |

The only real cost of MCP-only is that generation quality depends on the client's model. That is the owner's choice of client, and the validators bound the damage. **Recommendation: keep MCP-only; no decision to revisit.**

## Flow

```
 high-level prompt (text)
     |  0. Frame        LLM -> Brief: content target, tiers, hard constraints, open dimensions
     |  1. Explore      LLM uses catalogue queries; engine sweeps on 1-2 probe seeds
     |  2. Propose      LLM writes a Slate: 6-10 candidates, each a BuildSpec + mechanism claims + key pieces
     |  3. Gate         validate_slate: resolve, citations, PoE2-only, diversity; rejects return reasons
     |  4. Screen       cheap run per candidate (mid tier only), ablation of key pieces
     |  5. Deepen       top K (default 3) get the full run at all requested tiers
     v  6. Report       cross-archetype ranking on benchmark metrics, per tier, with why-it-works evidence
 slate_report.md + results.sqlite
```

### 0. Frame

The LLM turns the prompt into a `brief` block at the top of the slate: target benchmark(s) from `data/benchmarks.yaml`, tiers, hard constraints (named class, skill, "no minions", "hardcore-safe" = higher EHP floor), and which dimensions are **open** (free to vary). Anything the prompt fixes is a constraint; everything else is open. Ambiguities go back to the user only if they change the target content or tiers; otherwise the LLM picks and states the reading.

### 1. Explore: interaction discovery

Two kinds of tool, both read-only and cheap:

**Catalogue queries** (no engine). `search(kind, text=, skill_types=, tags=, ascendancy=, class=)` over the exported catalogue, plus three derived views:
- `enablers(skill_type)`: supports whose `add_types` grant a type (for example a support that makes a skill a totem or a trigger), and notables/keystones/unique lines whose text names it.
- `bridges(term_a, term_b)`: entries whose text mentions both terms (for example "Freeze" and "Lightning", "Armour" and "Energy Shield"). Cross-term co-occurrence is where non-obvious combinations live.
- `explain(kind, id)`: the entry's full PoE2 text (keystone/notable stats, unique mod lines, support `require/add/exclude` types). This is what the LLM must quote in a claim.

Gap found while designing: the catalogue has no unique mod lines and no gem descriptions (uniques are `{name, base, file}` only; text is fetched per item via engine `unique_text` during gear search). Task I2 adds both to the export so these queries run without an engine.

**Engine sweeps** on a probe seed (an assembled, supports-searched, tree-searched build with mid-tier placeholder gear):
- `sweep(seed, kind)`, kind in `keystone`, `unique:<slot>`, `support`, `ascendancy`: marginal delta of each catalogue entry on the target benchmark metric. Uniques use the `slot_item` fast path (57.6 evals/s measured in G4), so all uniques for one slot cost seconds; 33 keystones cost under a minute.
- Results are ranked deltas with the existing artefact flags: a single change above 3x is flagged for audit (G5 precedent: Fiery Death +20x was a FullDPS artefact), and an entry with exactly zero delta whose text claims an effect is flagged `possibly unmodelled`, not `useless`.

Sweeps surface interactions nobody asked for; the LLM then builds archetypes around the surprising positives. Probe seeds are chosen by the LLM from the brief (one per broad delivery type in play), at most 2 per slate to bound cost.

### 2. Propose: the Slate

```yaml
slate: 1
pob_sha: 601768b
prompt: "tanky lightning build that kills Arbiter on a budget"
brief:
  benchmarks: [arbiter_ash, breach_t15]
  tiers: [budget, mid]
  constraints: { damage_type: lightning }
  floors: { TotalEHP: 30000 }
candidates:
  - name: "Shock-stacking totems"
    archetype: { delivery: totem, damage: lightning, defence: armour+life, engine: shock }
    spec: { ... BuildSpec, docs/spec.md ... }
    key_pieces: [ { kind: keystone, id: "Ancestral Bond" }, { kind: support, id: "..." } ]
    claims:
      - text: "Totem limit doubled, so two totem stacks share the boss"
        cites: [ { kind: keystone, id: "Ancestral Bond", quote: "Your Totem Limit is doubled" } ]
    source: llm | sweep:<probe>/<entry>
```

`archetype` is a small fixed vocabulary, derived where possible rather than typed: `delivery` and `damage` from the main skill's `skill_types`, `defence` from fixed keystones/uniques and floors, `engine` free text (the one LLM-labelled field). `source` records which generator suggested it, so reports can show what each generator contributes.

The prompt asks for 8-12 candidates and the gate keeps at most 8 that pass, which substitutes for sampling control.

### 3. Gate: `validate_slate`

Deterministic, no engine, returns per-candidate errors with suggestions (same style as `validate`):

- **Spec**: each `spec` passes the existing validator (`docs/spec.md`).
- **PoE2-only names**: every name in spec, key pieces and cites resolves exactly in the pinned catalogue. Fuzzy suggestions are shown but never auto-applied. This catches PoE1 names that do not exist in PoE2.
- **Mechanism citations**: each claim cites at least one entry, and each `quote` is a substring (case- and whitespace-normalised) of that entry's catalogue text. This catches the subtler contamination: a name that exists in both games with a different effect, where the LLM describes the PoE1 behaviour. A claim with no quotable PoE2 text is rejected, and a claim that quotes correctly but states a number is rejected (numbers come only from the engine).
- **Key pieces**: 1-3 per candidate, each present in the candidate's spec (fixed keystone, notable, unique or support). These are what ablation removes.
- **Diversity**: pairwise distance over the archetype vector (class/ascendancy, delivery, damage, defence, main skill, key-piece set). Two candidates must differ on at least 2 of these 6 fields; the later one is rejected as a near-duplicate otherwise. The slate must also cover at least 3 distinct `delivery` or `damage` values when the brief leaves those open. Thresholds live in `data/ideation.yaml`, not code.
- **Rankability**: candidates whose skill has no metric (minion and buff-only skills, `data/metrics.yaml`) fail with `no_metric` until a metric exists, so they are not silently ranked on zero.

### 4. Screen

Per surviving candidate, one cheap orchestrator run: single tier (`mid`, or the brief's highest tier if lower), `--realloc-rounds 0`, tree cap 200, benchmarks from the brief. Then **ablation**: for each key piece, rebuild without it (keystone unallocated, unique replaced by the slot's best rare from the same search, support replaced by the next-best eligible) and re-evaluate the benchmark metric. Ablation verdicts:

- `confirmed`: removing it costs at least 10% (threshold in `data/ideation.yaml`) of the benchmark metric.
- `not load-bearing`: under the threshold. The claim may be true but does not drive this build; the report says so.
- `possibly unmodelled`: zero delta and the cited text describes an effect; points to an engine gap rather than a bad idea, and is added to `data/limitations.yaml` review.

Preflight uses `data/rates.yaml`; measured basis (Spark L90, 4 vCPU): supports ~29 s, tree ~23 s at cap 200, 9-slot gear ~1.2 min at realloc 0, ablation 1-3 short re-evals each. About 2.5 min per candidate, so a slate of 8 screens in ~20 min on 4 workers. Unverified on endgame builds; the preflight cap (45 min) applies to the whole slate.

### 5. Deepen

Successive halving: the top K (default 3) on the screen ranking get the normal full run (all brief tiers, realloc 4). K and the screening tier are slate options. Candidates that lose the screen stay in the report with their screen numbers, so a divergent idea that ranked fourth is still visible.

### 6. Rank and report

Per-skill DPS metrics are **not comparable across archetypes** (`TotalDPS` for one skill, `FullDPS` upper bound for another, `docs/spec.md`). Cross-archetype ranking therefore uses the benchmark metrics only: Arbiter time-to-kill with its survival gate, Breach clear proxy (`docs/benchmarks.md`), under one config profile per slate. While B3 inputs are unsourced, benchmark cells that are `incomplete` are shown as such and those candidates are ranked last with the reason, not ranked on a guess.

`slate_report.md`, per tier: ranked table (benchmark metrics, EHP, price estimate, archetype vector, `source`), and per candidate the claims with their quoted PoE2 text and ablation verdicts. Across the slate: which archetype wins at which tier, and which ideas came from the engine sweep rather than the LLM.

## Guardrails against PoE1 contamination (summary)

| Failure | Caught by |
|---|---|
| PoE1-only name (gem, unique, keystone, ascendancy) | exact catalogue resolution in `validate_slate` |
| Shared name, PoE1 behaviour described | quote-substring citation check against PoE2 catalogue text |
| Plausible mechanic PoB does not model | ablation `possibly unmodelled` flag + `data/limitations.yaml` |
| Invented numbers | claims with numbers rejected; reports quote engine output only |
| Engine artefact mistaken for a synergy | >3x single-change audit flag carried from G5; FullDPS labelled upper bound |

A PoE1-name denylist is not built now: exact resolution already rejects absent names. Per the project rule, a contamination slip seen twice becomes a check.

## Interface additions (MCP + CLI)

| MCP tool / prompt | CLI | Notes |
|---|---|---|
| prompt `ideate` | - | procedure text, slate schema, the rules above; Opus writes, Fable reviews |
| `search`, `enablers`, `bridges`, `explain` | `pos catalogue search ...` | read-only, catalogue only |
| `sweep` (async) | `pos sweep spec.yaml kind` | engine, probe seed |
| `validate_slate` | `pos slate validate slate.yaml` | deterministic |
| `run_slate` (async, run id), reuses `run_status`, `get_report` | `pos slate run slate.yaml [--preflight]` | screen -> ablate -> deepen |

## Decisions made here (technical, reversible, no card)

Two generators (LLM + engine sweeps); slate as a list of BuildSpecs rather than a new spec axis (archetypes differ in class and skill, which axes do not span); quote-substring citation check; diversity as a distance over a fixed archetype vector; screen-then-deepen with K=3; cross-archetype ranking on benchmark metrics only; minion/buff candidates excluded until they have a metric.

Known weaknesses (judgement): the archetype vector is coarse, so two candidates can pass diversity and still play alike; sweeps are one-change-at-a-time and miss pairs that only work together (the LLM proposes those, ablation checks them); screening at one tier can drop an idea that only shines at high budget (mitigation: screening tier is a slate option).

## Implementation tasks

Each sized to a brief under 20k tokens and a finish under 150k. Model: Sonnet unless noted.

| Id | Task | Depends on |
|---|---|---|
| I2 | Catalogue export: unique mod lines and gem descriptions/stat text; `search` / `enablers` / `bridges` / `explain` in `pos_catalogue` + CLI + tests; repin diff covers the new fields | G2 |
| I3 | Slate schema + `validate_slate` (resolution, quote citations, number-in-claim rejection, key pieces, diversity distance, rankability) + `data/ideation.yaml` thresholds + CLI + tests | I2, G3a |
| I4 | `sweep` (keystone, unique per slot via slot_item, support, ascendancy) on a probe seed with artefact/unmodelled flags; `ablate(build, key_pieces)` with verdicts; CLI + tests; measure sweep time on Spark | G3b, G4, G5, G6 |
| I5 | Slate runner: screen (one tier, cheap settings) + ablation + successive halving into full runs; slate preflight; cross-archetype ranking on benchmark metrics; `slate_report.md` + sqlite tables; golden test | I3, I4, G8b |
| I6 | MCP: `ideate` prompt + the tools above on the G9 server; usage guide section. Opus writes the prompt and tool text | I5, G9 |
| I7 | Evaluation (Opus): 5 fixed high-level prompts end to end; record resolve-failure rate, citation rejections, PoE1 slips caught, diversity, share of `confirmed` ablations, engine-sourced vs LLM-sourced winners; tune `data/ideation.yaml` | I6 |

I2 can start now. I4 can start in parallel with I2/I3 (it needs only merged stages).
