# Benchmarks: boss and mass-mob content (B1)

Status: design, 2026-11-22. Owner requirement (cmsg_01RxGYnd78N9kMbbAJ5pWDhUEhCn1kwfA6vy3QYah3EvbX): sim builds against benchmark content, starting with one hard endgame boss and one endgame mass-mob content. Content decided by the owner 2026-11-22: Arbiter of Ash + Breach T15+ (cmsg_01RxGYnd78N9kMbbAJ5pWDhUEx7vFAPsHTmhjjy3Gx6rKW).

## 1. What existing tools model (checked)

Checked in code at PoB-PoE2 `601768b` (our pin) and shallow clones of the cited projects, 2026-11-22.

| Tool | Boss time-to-kill | Survival vs boss hits | Clear speed vs packs |
|---|---|---|---|
| PoB-PoE2 | **no.** No enemy life pool for bosses; `monsterLifeTable` is used only for corpse/explosion skills (`CalcOffence.lua` ~1978, ~2410). | **partly, statically.** `enemyIsBoss` (None/Boss/Pinnacle/Uber) sets enemy res, armour/evasion and a generic hit size; raw overrides exist per type (`enemyPhysicalDamage`, `enemyFireDamage`, ..., `*Pen`, `enemySpeed`, `enemyCritChance`, `enemyDamageType`). Outputs: `TotalEHP`, `TotalNumberOfHits`, `EHPSurvivalTime`, `<Type>MaximumHitTaken`, `<Type>DotEHP`, `NetLifeRegen`. The `presetBossSkills` list (`Data/BossSkills.lua`) is **PoE1 content only** (Atziri, Shaper, Sirus, Exarch, Eater, Maven): unusable for PoE2. | **no.** It reports `AreaOfEffectRadius`, `AverageHit`, `ProjectileCount`, speed; nothing about packs. |
| MaxWilk/poe2-build-mcp | no; `BUILD_ADVICE.md` says the real test is "time-to-kill on the content the player wants" but nothing computes it | `apply_boss_profile` (sets `enemyIsBoss` + charge/shock/curse toggles); `pinnacle_readiness` = fixed gates (default EHP >= 20k, DPS >= 500k) | no |
| HivemindOverlord/poe2-mcp | no (culling/stun notes are text) | no | `gear_optimizer` accepts goal `clear_speed`/`boss_damage`, but over its own non-PoB calculators (excluded in docs/prior-art.md) |
| SFerenczy/poe2-agent | no | no | "clear speed" appears only in LLM prompt text |

Conclusion (fact): nobody models encounters. PoB supplies the static ingredients (hit damage, DPS under an enemy profile, max hit per damage type, hits-to-die, AoE radius); time-to-kill, survival against a named hit profile, and clear speed are a model layer we build on top.

## 2. Candidate content (current patch 0.5.x; numbers change at 1.0 on 2026-12-11)

Sources are secondary guides unless stated; "community" = heuristic, not GGG data. Pinnacle bosses in 0.5.2 (Switchblade, modified 2026-10-10): Arbiter of Ash (+ uber), Arbiter of Divinity, King in the Mists, Xesht, Olroth, Omniphobia/Kosis (Simulacrum), Vessel of Kulemak, Zarokh/Trialmaster.

### Boss candidates

| Boss | Life | Damage profile | Community bar | Why / why not |
|---|---|---|---|---|
| **Arbiter of Ash** (pinnacle; uber variant) | 4,274,058 at level 74, res fire/cold/lightning/chaos 30/-30/0/0, armour 4,099 ([poe2db](https://poe2db.tw/sp/The_Burning_Monolith), game-file derived, id `MapUberBoss_Monolith`); guides say ~5M, uber >22M (community; uber not on poe2db page) | physical + fire; phase 2 at 55% has sword combos that "chunk 50%+" of life | fire res 75% (80-85% advised), 5k life / 10k ES, 1M+ DPS | Phys+fire hit profile that exercises armour and fire res, and an uber tier that gives a natural "hard" setting. **Recommended.** |
| Arbiter of Divinity | not checked (poe2db likely has it) | lightning-heavy (87%+ lightning res advised); invulnerable/regen phase at 40% | 6k life / 12k ES, 1M+ | Harder on paper, but the invulnerable/regen phase makes TTK depend on fight script, not DPS. |
| Xesht, We That Are One | not checked (poe2db likely has it) | void overlays; four difficulty tiers | 4k life / 8k ES, 500k+ | Tiers are attractive; easier bar; void overlays are not a PoB damage type. |

### Mass-mob candidates

| Content | Structure | Why / why not |
|---|---|---|
| **Breach in a tier-15+ waystone** | dense waves spawning outward from a point under a short timer; on most maps (Switchblade) | Pure density + kill rate under a clock: the case where AoE radius and hits-to-kill on magic/rare monsters decide value. Commonest juiced farm. **Recommended.** |
| Simulacrum (Delirium) | 7 waves in 0.5 (Switchblade; Maxroll 2024 said 15), escalating monsters, fixed arena | Also stresses sustained survival, but wave scaling is unpublished and the boss (Kosis/Omniphobia) mixes a boss test into it. Good second mob benchmark later. |
| Ritual / Abyss / Expedition | mixed packs | Less density-driven; skip for v1. |

Monster life base (primary, game data via PoB `Data/Misc.lua` from `DefaultMonsterStats.dat`): level 82 = 32,956, level 83 = 33,945, level 84 = 34,963. Rarity and map-mod life multipliers are **not** in PoB and not yet sourced; they are inputs with a `source: unverified` label until read from game files (poe2db monster pages or a GGPK export).

## 3. Model layer

All derived numbers come from PoB outputs plus a labelled benchmark constant; no LLM-supplied number (pipeline principle).

### 3.1 Benchmark definition: `data/benchmarks.yaml`

```yaml
schema_version: 1
benchmarks:
  arbiter_ash:                      # id used in specs and reports
    kind: boss
    patch: "0.5.2"                  # data stamp; report prints it; stale after 1.0 (section 4)
    pob_options:                    # applied with set_config; hash joins the cache key like config profiles
      enemyIsBoss: Pinnacle         # 'Uber' for arbiter_ash_uber
      enemyLevel: 74                # poe2db row; note PoB clamps Pinnacle to >= 82, so B2 must use enemyIsBoss + explicit overrides and check what PoB applies
      enemyFireResist: 30
      enemyColdResist: -30
      enemyLightningResist: 0
      enemyChaosResist: 0
      enemyArmour: 4099
    life: { value: 4_274_058, source: "poe2db.tw/sp/The_Burning_Monolith (MapUberBoss_Monolith), 0.5.x" }   # guides say ~5M
    uptime: { value: 0.75, source: "ASSUMPTION: share of fight the boss is hittable and the player is attacking" }
    hits:                           # named hits to survive; each is one PoB evaluation with enemy damage overridden
      - { name: phase2_sword_combo, physical: null, fire: null, source: "TODO: poe2db skill multipliers x monsterDamageTable[82]" }
    gates: { ttk_s_max: 60, survive_all_hits: true }   # 60 s is an ASSUMPTION, owner-tunable
  breach_t15:
    kind: pack
    patch: "0.5.2"
    pob_options: { enemyIsBoss: None, enemyLevel: 83 }
    monsters:                       # life = monsterLifeTable[level] x mult
      - { rarity: normal, count: 40, life_mult: 1.0, source: "PoB Misc.lua base; count assumed" }
      - { rarity: magic,  count: 12, life_mult: null, source: "TODO game data" }
      - { rarity: rare,   count: 3,  life_mult: null, source: "TODO game data" }
    spread_radius_m: 6.0            # assumed pack footprint radius
    gates: { clear_s_max: 20 }
```

A `null` value means "not sourced": the validator fails the benchmark instead of guessing, except where a PoB default stands in and the report says so.

### 3.2 Metrics (`pos_pipeline/benchmarks.py`, task B2)

Boss:
- `ttk_s = life / (DPS_metric x uptime)`, with DPS_metric the per-skill metric (data/metrics.yaml) evaluated under the benchmark's `pob_options`. DoT ailments: use `FullDPS` where it includes them; the report labels which.
- `hit_margin[h] = min over damage types of <Type>MaximumHitTaken / hit[h].<type>` evaluated with that hit's damage set via `enemy*Damage`; survive = margin >= 1. Until hits are sourced, fall back to PoB's Pinnacle/Uber generic hit and label it "generic".
- Also reported: `TotalEHP`, `TotalNumberOfHits`, `EHPSurvivalTime` under the benchmark profile.
- Note: TTK is a monotone function of DPS, so on its own it ranks builds exactly as DPS does. The benchmark adds information only through the absolute gate (does this tier kill it in time) and the named-hit survival check, which is why sourcing hits (B3) is the core value, not a follow-up.

Pack (a **density proxy**, not real seconds; nothing in it is Breach-specific: the content id only fixes level, counts and footprint):
- `hits_to_kill[r] = ceil(life[r] / AverageHit)` under the pack profile (hit chance and crit included by PoB's average hit).
- `coverage = min(1, (AoE_radius_m / spread_radius_m)^2)` per cast, with `ProjectileCount` raising effective coverage for projectile skills (capped at 1); radius from `AreaOfEffectRadiusMetres`.
- `clear_s = max_r(hits_to_kill[r]) / coverage / Speed`: casts until every monster in the footprint has taken enough hits, assuming each cast hits a `coverage` share of the pack, divided by casts (or attacks) per second.
- Explicitly not modelled: movement between packs, monster movement, on-kill effects (explosions, chains), proliferation of ailments. These dominate real clear speed, so the proxy ranks raw AoE kill power only. Report says so.
- Swarm survival: v1 has none. Planned: EHP under many simultaneous normal-monster hits (`enemyIsBoss: None`, damage x hits-per-second at the pack's level) as `TotalNumberOfHits`/`EHPSurvivalTime`; until then the report states the absence.

Engine change: add `AverageHit`, `AreaOfEffectRadiusMetres`, `TotalNumberOfHits`, `EHPSurvivalTime`, `PhysicalMaximumHitTaken`, `FireMaximumHitTaken`, `ColdMaximumHitTaken`, `LightningMaximumHitTaken`, `ChaosMaximumHitTaken` to `stat_keys` (wrapper list + metrics.yaml test). Cost: one extra evaluation per benchmark profile per variant, plus one per named hit for survival (cheap; the hit checks only need defensive outputs).

### 3.3 Pipeline integration

- **Spec**: `benchmarks: [arbiter_ash, breach_t15]` (default: both). `config_profile` remains for the search objective; each benchmark re-evaluates the shortlisted variants under its own `pob_options` (cache key = build hash + benchmark options hash).
- **Search**: unchanged by default (maximise the per-skill metric under `pinnacle_boss`, with floors). Option `objective: { minimise: ttk_s@arbiter_ash, floors: { survive@arbiter_ash: true } }` lets the search optimise a benchmark directly; validator checks the benchmark exists and its required values are sourced.
- **Report**: per tier, a benchmark table: TTK (s), hit margins (pass/fail), EHP; pack hits-to-kill per rarity, coverage, clear-time proxy; each with its `patch` and `source` labels, and "generic hit" / "assumed" flags in the cell.

## 4. 1.0 update path

- Every benchmark constant carries `patch` and `source`. `tools/repin.sh` (G10) gains a check: if the pinned PoB's game version differs from a benchmark's `patch`, the repin report lists it as stale and reports mark those numbers "stale".
- Base monster life, damage, armour and evasion tables update automatically with the PoB re-pin (they come from `Misc.lua`).
- Boss life, hit multipliers, rarity multipliers: re-read after 1.0 from poe2db.tw monster pages (game-file derived) or a GGPK export. Expected change: new or re-tuned pinnacle fights at 1.0; the benchmark ids stay, values are replaced, and a different boss can be swapped in with one YAML entry.

## 5. Decision (made: option A)

Which content to standardise on first. Owner chose A on 2026-11-22. Recommendation was (judgement): **Arbiter of Ash (pinnacle, uber as the hard setting) + Breach in a tier-15+ waystone.** Arbiter has a phys+fire hit profile that tests two defensive layers and an uber tier for the hard setting; Breach isolates density and kill rate, which is what a clear-speed proxy can actually rank. Alternatives: Arbiter + Simulacrum (adds sustained survival, but unpublished wave scaling), or Xesht + Breach (easier bar, tiers, void overlays PoB has no type for). Boundary: if "hard" means the single hardest fight, Arbiter of Divinity wins on paper but its invulnerable phase makes TTK script-bound.

Sequencing (judgement, reversible, no card): build B2 now with content ids that are swappable data; source hit profiles and multipliers (B3) against 1.0 data on poe2db after 2026-12-11 rather than 0.5 numbers that will be replaced. Nothing found yet says whether Arbiter, uber tiers or Breach persist at 1.0; if not, the nearest equivalents take the same ids' roles.

Advisor review (2026-11-22) corrected the first draft: poe2db carries game-file life/res rows for pinnacle bosses, so "only fight with a life figure" was wrong; the draft YAML used guide life and PoB defaults; TTK alone duplicates DPS ranking; the pack model is a density proxy without survival.

## 6. Tasks

| Id | Task | Needs |
|---|---|---|
| B2 (done) | `data/benchmarks.yaml` + loader/validator + `pos_pipeline/benchmarks.py` metrics + engine `stat_keys` additions + tests (Sonnet) | owner content choice |
| B3 | Source hit profiles, uber life and rarity life multipliers from game data (poe2db or GGPK) for the chosen content; reconcile with PoB's level clamp; fill `null`s | B2 + 1.0 data on poe2db (after 2026-12-11) |
| B4 | Report columns + spec `benchmarks:` / benchmark objective (folds into G8b) | B2 |
| B5 | repin.sh stale-benchmark check | B2 |

Sources: [Switchblade pinnacle guide (0.5.2, modified 2026-10-10)](https://www.switchbladegaming.com/path-of-exile-2/endgame-boss-guide/), [Timesaver Arbiter of Ash guide (0.5, updated 2026-06-24)](https://timesaver.gg/blog/poe2-arbiter-of-ash-guide), [Maxroll pinnacle bosses (2024, pre-0.5)](https://maxroll.gg/poe2/resources/pinnacle-bosses); PoB-PoE2 `601768b`: `src/Modules/ConfigOptions.lua`, `src/Data/BossSkills.lua`, `src/Data/Misc.lua`, `src/Modules/CalcDefence.lua`.

B2 as built: YAML cells are `{value, source}`; `null` = unsourced. Survival uses `<Type>MaximumHitTaken / hit damage` from one evaluation per benchmark (max hit does not depend on enemy damage), so no per-hit evaluation was needed; while hits are null, `survive` is None and PoB's generic `TotalNumberOfHits` is shown. Pack `clear_s` stays None until every rarity's `life_mult` is sourced. Projectile skills without an AoE radius use coverage = projectiles / monsters. Not yet checked: which of `enemyLevel`/res/armour overrides PoB applies on top of `enemyIsBoss: Pinnacle` (B3).
