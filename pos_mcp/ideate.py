"""The `ideate` MCP prompt (I6, docs/ideation.md). The procedure text is fixed; the vocabulary (pinned data sha, benchmark
ids, tiers, slots, thresholds) is read from data files at call time, so it stays true after a re-pin or a threshold change.
Grounding is enforced by `validate_slate` and the runner; this text only steers the client model towards slates that pass."""
from __future__ import annotations

from typing import Any

PROCEDURE = """\
# Ideate PoE2 builds for: {idea}
{constraints_line}
Goal: propose genuinely different build archetypes for this idea, then let the engine (Path of Building on pinned PoE2
data {sha7}) measure them. Divergence is the point: a slate of near-copies of one popular build fails. Your ideas are
hypotheses; the engine and the slate gate decide what is true.

## Hard rules (the gate rejects violations; do not try to argue past it)
1. PoE2 only. Your memory of Path of Exile is mostly PoE1: names, mechanics and numbers from PoE1 are wrong here. Treat
   every game name you remember as a guess until `resolve` returns it as `exact` (or it came back from `search`,
   `enablers`, `bridges` or `explain`). If a name is unresolved, use a suggestion or drop the idea; never respell it to
   force a match. Skills that share a name with a PoE1 skill can work differently: read `explain` before relying on one.
   If the user's own idea names something that does not resolve (for example a PoE1 skill), tell the user in one line
   that it is not in this PoE2 data, name the PoE2 substitute you use for each candidate, and keep the idea's intent.
2. Every mechanism claim cites PoE2 text. A cite is {{kind, id, quote}} where `quote` is copied verbatim from a `text` line
   of `explain(kind, id)` (at least {quote_min} characters). Paraphrase in `text`, never in `quote`. Quote the
   clause that carries the condition too: a quote cut off before "if", "while" or "count as ..." passes the gate but
   misstates the mechanic. Ascendancy passives are notables: find them with `search(kind='notable', ascendancy=...)`.
3. No numbers you made up, anywhere. Claims may not contain digits, % or number words ({number_words_sample}, ...).
   Quotes are exempt (verbatim game text may contain numbers). Do not estimate DPS, EHP, time-to-kill, clear speed
   or prices in chat either. Numbers come only from
   `get_report`; quote them from there, with the benchmark or tier they belong to.
4. Rankable skills only: the main skill must deal damage itself. Minion and buff-only main skills have no metric yet and
   are rejected (`no_metric`); say so if the idea needs one, and offer the nearest damage-dealing take.
5. 1-3 `key_pieces` per candidate (keystone, notable, unique or support), each also fixed in that candidate's spec. They
   are the pieces your claims say the build depends on; the runner removes each one and measures the loss.

## Step 0. Frame (no tools)
Write the brief: which benchmarks ({benchmark_list}), which tiers ({tier_list}), hard constraints the user stated, and
which dimensions stay open (class/ascendancy, delivery, damage type, defence layer, main skill). Anything the user did
not fix is open. Only ask the user when the content target or budget is genuinely unclear; otherwise choose, and state
the reading in one line. Default: benchmarks [arbiter_ash, breach_t15], tiers [mid].

## Step 1. Explore (cheap, read-only; spend most of your effort here)
- `search(kind, text=...)`: candidates by word, type or tag. `explain(kind, name)`: full text to quote.
- `bridges(term_a, term_b)`: entries whose text names both terms. Pair terms from different domains (a defence word
  with a damage word, an ailment with a delivery, a resource with a skill type); co-occurrence is where non-obvious
  combinations live. Try several pairs, not one.
- `enablers(skill_type)`: supports that add a skill type to what they support (for example `CreatesGroundEffect`,
  `GeneratesCharges`, `ConsumesCharges`, `SkillConsumesFreeze`) and passives or uniques that name it. Skill types are
  exact catalogue names; read real ones from `explain(kind='skill')` or `explain(kind='support')`.
- Optional, engine: `sweep(spec, kind)` on at most two probe specs (keystone | ascendancy | support | unique:<slot>),
  about one to two minutes each, one job at a time. The probe seed carries no gear, so an attack main skill cannot
  be evaluated (`probe seed failed to evaluate`): probe with a spell main skill, or skip the sweep. Entries with a large positive delta are leads you did not think
  of. The metric is damage, so defensive entries show zero by design; `possibly_unmodelled` on an entry whose text
  should raise damage means PoB may not model it (label it, do not call it a dud); `audit_outlier` means check for an
  engine artefact first; `over_budget` deltas are added on top of a full tree, not traded for other points. Build at least one candidate on a sweep lead when you ran a sweep, with
  `source: "sweep:<probe>/<entry>"`.

## Step 2. Propose a slate of {n_lo}-{n_hi} candidates
Make them differ in kind, not degree. For each, name its "engine" in a few words: the one interaction that makes it
work. Spread across delivery (self-cast, projectile, area, channel, melee, totem, trap, mine), damage type, defence
layer and class/ascendancy. Include at least one idea a typical player would not try first. Two candidates must
differ on at least {min_diff} of: class/ascendancy, delivery, damage, defence, main skill, key-piece set; and the kept
set must cover at least {min_distinct} distinct deliveries or damage types unless the user fixed both.
Slate YAML (spec schema = `validate_spec`; `delivery` and `damage` are derived from the skill and may be omitted):

```yaml
slate: 1
pob_sha: "{sha7}"
prompt: "<the user's idea, verbatim>"
brief: {{ benchmarks: [arbiter_ash], tiers: [mid], constraints: {{}}, floors: {{}} }}
candidates:
  - name: "<short, distinct>"
    archetype: {{ defence: <armour | evasion | energy_shield | life | ...>, engine: "<the interaction, in words>" }}
    spec: {{ pob_sha: "{sha7}", class: <exact>, ascendancy: <exact>, level: 90, main_skill: {{ gem: <exact> }},
            tiers: [mid], fixed: {{ keystones: [], notables: [], uniques: [], supports: [] }} }}
    key_pieces: [ {{ kind: keystone, id: <exact name> }} ]
    claims:
      - text: "<what it does for this build, no numbers>"
        cites: [ {{ kind: keystone, id: <exact name>, quote: "<verbatim from explain text>" }} ]
    bases: {{ weapon: <exact base> }}      # optional; slots: {slots}
    source: llm                           # or sweep:<probe>/<entry>
```

Gear: the runner searches rares in the slots given in `bases` (per candidate, or the `bases` argument of `run_slate` as
a default). Give each candidate a weapon base its main skill can use (`explain` the skill: a Bow skill needs a bow, a
Spear skill a spear; resolve the base with kind 'base'); a shared default only suits candidates with the same weapon
type. Give a body armour base matching the candidate's defence layer as well (and an amulet if the budget allows): a
weapon-only screen leaves life, defences and resistances near zero, so every candidate fails the boss survival check
and the ranking says little. A fixed unique in a searched slot is overwritten and its ablation becomes `not_testable`: put fixed uniques in
slots you do not search.

## Step 3. Gate
`validate_slate(slate)`. For each rejected candidate, fix the cause from the issue codes and suggestions (unresolved
name, quote_mismatch, claim_number, near_duplicate, no_metric, key_piece_not_in_spec) or replace it with a different
idea. At most three rounds; then continue with what is kept. The gate keeps at most {max_kept}. Do not weaken a claim
into something vague just to pass: drop the claim or the candidate instead.

## Step 4. Show, estimate, run
Show the user the kept candidates as a short table: name, class/ascendancy, main skill, engine, key pieces, source.
Then `preflight_slate(slate, bases)` and give the estimate. If it is within the cap, start `run_slate(slate, bases)`
unless the user asked for ideas only; if over the cap, offer to cut candidates or deepen_k, or to force. Poll
`run_status` about once a minute (screening is several minutes per candidate).

## Step 5. Report
`get_report(run_id)`, then summarise: which archetype ranks first per benchmark and tier, using the report's numbers
only. Ranking is on benchmark metrics; per-skill DPS is not comparable across archetypes, so do not rank on it.
For each candidate give the ablation verdicts plainly: `confirmed` = the key piece carries the build;
`not_load_bearing` = the premise was not borne out (say so); `possibly_unmodelled` = PoB may not model it, so the
number may understate the idea; `not_testable` = why. Read out incomplete benchmarks, unsourced inputs and
limitations instead of smoothing them over. Say which ideas came from sweeps and which from you.
"""


def render(idea: str, constraints: str = "") -> str:
    from pos_catalogue import Catalogue
    from pos_pipeline import data
    from pos_pipeline.benchmarks import benchmarks, validate_benchmark
    from pos_pipeline.gear import SLOTS
    from pos_tiers.tiers import TierTable

    cfg = data.ideation()
    sha7 = Catalogue.load().pob_sha[:7]
    bms = []
    for bid, b in benchmarks().items():
        _, unsourced = validate_benchmark(bid)
        bms.append(f"`{bid}` {b['kind']}" + (" - incomplete, unsourced inputs" if unsourced else ""))
    tier_list = ", ".join(f"`{t}`" for t in TierTable.load().tier_names)
    max_kept = cfg["slate"]["max_kept"]
    return PROCEDURE.format(
        idea=idea.strip() or "(no idea given: ask the user for one line)",
        constraints_line=f"User constraints: {constraints.strip()}\n" if constraints.strip() else "",
        sha7=sha7, quote_min=cfg["slate"]["quote_min_chars"],
        number_words_sample=", ".join(cfg["number_words"][:6]),
        benchmark_list="; ".join(bms), tier_list=tier_list,
        n_lo=max(cfg["slate"]["min_candidates"], 6), n_hi=max_kept + 2, max_kept=max_kept,
        min_diff=cfg["diversity"]["min_differing_fields"], min_distinct=cfg["diversity"]["min_distinct"],
        slots=", ".join(SLOTS) + " (`ring` sets both)")

