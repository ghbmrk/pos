"""MCP server (stdio). `python -m pos_mcp`. Tool descriptions are the contract the LLM client reads: keep them exact."""
from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from . import core, ideate as _ideate

INSTRUCTIONS = """Path of Sim: test PoE2 build ideas with real Path of Building calculations on pinned PoE2 data, at gear price tiers,
against benchmark content (a pinnacle boss and a dense map pack).
Ground rules for every path: (a) game names come only from the catalogue (`resolve` exact, or the query tools); your memory
of Path of Exile is mostly PoE1 and is wrong here. (b) Numbers (DPS, EHP, time-to-kill, prices) come only from reports;
never estimate them. (c) Read limitations, unsourced inputs and incomplete benchmarks out to the user.
Two paths:
1. The user names a build ("test Spark Stormweaver"): resolve names -> validate_spec until ok -> preflight (tell the user
   the estimate) -> run with a base per gear slot -> run_status about once a minute -> get_report and summarise.
2. The user gives a goal, not a build ("a tanky lightning build that kills Arbiter on a budget", "something creative
   with ..."): call `ideation_guide` with their words first and follow it (catalogue queries, a slate of distinct
   archetypes, validate_slate, preflight_slate, run_slate). The same procedure is the `ideate` prompt.
One background job (run, sweep or slate) at a time; they share the CPUs."""

mcp = MCPServer("path-of-sim", instructions=INSTRUCTIONS)


# ---- naming and specs -------------------------------------------------------------------------------------------
@mcp.tool()
def resolve(kind: str, names: list[str], pob_sha: str | None = None) -> dict[str, Any]:
    """Look up game names in the pinned PoE2 catalogue. kind: class | ascendancy | skill | support | unique | base | keystone | notable.
    Per name: status exact | ambiguous | unresolved, plus near-match suggestions. Only exact matches may go in a spec or slate.
    Never respell a name to force a match: pick a listed match/suggestion (ask the user if they named it themselves), or drop the idea.
    A name that does not resolve is usually PoE1-only."""
    return core.resolve(kind, names, pob_sha)


@mcp.tool()
def validate_spec(spec: str | dict[str, Any]) -> dict[str, Any]:
    """Validate a build spec (YAML text or object) against the catalogue and the engine's known limits. Returns ok, the metric the run
    ranks by, and issues (error/warning with code and suggestions). Fix every error before `run`; tell the user about warnings and
    'limitation' issues. Required: pob_sha, class, level, main_skill {gem}, tiers (from: starter, budget, mid, high, mirror).
    Optional: ascendancy; fixed {supports, keystones, notables, uniques} (lists of exact names); axes (ascendancy | main_skill |
    weapon_base -> list of values, one seed per combination); objective {maximise, floors}; config_profile; benchmarks
    (arbiter_ash, arbiter_ash_uber, breach_t15). Minion and buff-only main skills have no metric yet (error no_metric)."""
    return core.validate_spec(spec)


@mcp.tool()
def import_pob(code: str) -> dict[str, Any]:
    """Convert a Path of Building share code (or build XML) into a draft spec (YAML) plus warnings for anything dropped
    (gear is not carried over: the run searches it). Edit the draft, then validate_spec."""
    return core.import_pob(code)


# ---- single-build runs ------------------------------------------------------------------------------------------
@mcp.tool()
def preflight(spec: str | dict[str, Any], bases: dict[str, str] | None = None, workers: int | None = None,
              realloc_rounds: int | None = None) -> dict[str, Any]:
    """Estimate wall time of `run` without running (also validates). bases maps gear slot -> exact base name (resolve kind 'base'),
    e.g. {"weapon": "Acrid Wand", "amulet": "Lapis Amulet"}; slots: weapon, body, amulet, ring_1, ring_2, helmet, gloves, boots, belt
    (`ring` sets both). Cost grows with slots, seeds (axes combinations) and tiers. over_cap=true: the run will be refused unless
    forced; give the user the estimate and let them decide."""
    return core.preflight(spec, bases, workers, realloc_rounds)


@mcp.tool()
def run(spec: str | dict[str, Any], bases: dict[str, str], workers: int | None = None, realloc_rounds: int | None = None,
        max_minutes: float | None = None, force: bool = False, allow_assumed: bool = False, rounds: int = 1) -> dict[str, Any]:
    """Start a single-build run in the background (supports, passive tree, then gear per tier; minutes to tens of minutes) and return a
    run_id at once. Validates first; refuses an invalid spec, missing bases, or an estimate above the cap (default 45 min) unless
    force=true, which you set only after the user has seen the estimate. realloc_rounds=0 is a cheaper, weaker gear search.
    rounds>1 adds the improvement loop (L3): supports, tree and gear are re-searched from the geared build, each result kept only if the
    benchmark objective improves, until a round gains <1% or `rounds` ran; the estimate then shows an upper bound. trace.jsonl in the run dir.
    One background job at a time. Then poll run_status and call get_report.
    A spec with `companion.assumed` is an ASSUMED Squire what-if (invented effects, not game data; docs/squire-assumed.md): it runs only
    with allow_assumed=true, which you set only when the owner asked for such a what-if; always quote its ASSUMED banner with any number."""
    return core.start_run(spec, bases, workers=workers, realloc_rounds=realloc_rounds, max_minutes=max_minutes, force=force,
                          allow_assumed=allow_assumed, rounds=rounds)


@mcp.tool()
def run_status(run_id: str) -> dict[str, Any]:
    """State of any background job (run, sweep or slate): running | done | failed | cancelled, elapsed seconds, the estimate,
    and the last log lines. Poll about once a minute, not faster. On failed, show the user the log tail."""
    return core.run_status(run_id)


@mcp.tool()
def cancel_run(run_id: str) -> dict[str, Any]:
    """Stop a running background job (run, sweep or slate) and all its engine processes."""
    return core.cancel_run(run_id)


@mcp.tool()
def get_report(run_id: str, max_chars: int = 20000) -> dict[str, Any]:
    """The finished job's report (markdown). Run: per tier the best variants with DPS/EHP/resists, gear, supports, benchmark results,
    price labels, limitations, and which axis value wins at which budget. Slate: candidates ranked on benchmark metrics with
    ablation verdicts. Sweep: one-change-at-a-time deltas on a probe seed. These numbers are the only ones to quote, with their
    labels (tier, benchmark, 'upper bound', 'incomplete')."""
    return core.get_report(run_id, max_chars)


@mcp.tool()
def compare(run_a: str, run_b: str, include_assumed: bool = False) -> dict[str, Any]:
    """Best result per tier in two finished single-build runs and the % delta. Only meaningful when both used the same metric
    (returned note says when they differ); for different archetypes compare benchmark results in the reports instead.
    ASSUMED Squire what-if runs are refused unless include_assumed=true."""
    return core.compare(run_a, run_b, include_assumed)


@mcp.tool()
def list_runs(limit: int = 10, include_assumed: bool = False) -> dict[str, Any]:
    """Recent background jobs: run_id, job (run | sweep | slate), state. ASSUMED Squire what-if runs are hidden unless include_assumed=true."""
    return core.list_runs(limit, include_assumed)


# ---- ideation (docs/ideation.md) ------------------------------------------------------------------------------
@mcp.prompt(name="ideate", title="Ideate PoE2 builds",
            description="Turn a high-level goal into a slate of distinct, catalogue-grounded build archetypes, gate them, and run them.")
def ideate(idea: str, constraints: str = "") -> str:
    return _ideate.render(idea, constraints)


@mcp.tool()
def ideation_guide(idea: str, constraints: str = "") -> str:
    """The step-by-step procedure for open-ended requests (a goal rather than a named build): explore the catalogue, propose a slate
    of distinct archetypes with PoE2 text citations, gate it with validate_slate, run it with run_slate, report. Call this first
    and follow it. Same text as the `ideate` prompt, with the current benchmark ids, tiers and thresholds filled in."""
    return _ideate.render(idea, constraints)


@mcp.tool()
def search(kind: str, text: str | None = None, skill_types: list[str] | None = None, tags: list[str] | None = None,
           ascendancy: str | None = None, class_name: str | None = None, limit: int = 25) -> dict[str, Any]:
    """Find catalogue entries of one kind (skill | support | unique | keystone | notable | base | ascendancy | class). Filters AND
    together. text: words that must each start a word in the name or game text ('freez' finds Freeze/Frozen; lexical, not semantic).
    skill_types: exact catalogue skill types (e.g. Spell, Projectile, Channel; read real ones from explain). tags: gem or base tags.
    ascendancy: notables of that ascendancy. class_name: ascendancies of that class. Returns names with trimmed text."""
    return core.search(kind, text, skill_types, tags, ascendancy, class_name, limit)


@mcp.tool()
def bridges(term_a: str, term_b: str, limit: int = 10) -> dict[str, Any]:
    """Entries (keystones, notables, uniques, supports, skills) whose name or text mentions both terms, e.g. ('Armour', 'Lightning')
    or ('Ignite', 'Minion'). Pairing terms from different domains surfaces non-obvious combinations; co-occurrence is lexical,
    so read the text and judge."""
    return core.bridges(term_a, term_b, limit)


@mcp.tool()
def enablers(skill_type: str, limit: int = 15) -> dict[str, Any]:
    """What grants or names a skill type: supports that add it to the skill they support (e.g. CreatesGroundEffect, GeneratesCharges,
    SkillConsumesFreeze), plus keystones, notables and uniques whose text names it. skill_type is an exact catalogue type name
    (case-sensitive; read real ones from explain)."""
    return core.enablers(skill_type, limit)


@mcp.tool()
def meta_lessons(pattern: str | None = None) -> dict[str, Any]:
    """Compounding patterns that carried past PoE1/PoE2 metas (stat stacking, conversion funnels, trigger loops, layered
    defences, ...): mechanism, why it compounds, limits, era and evidence, PoE2 starting points verified on the pinned data
    and the probe levers it should move. Past build names are left out on purpose. Cite ids in archetype.patterns."""
    return core.meta_lessons(pattern)


@mcp.tool()
def explain(kind: str, name: str) -> dict[str, Any]:
    """Full PoE2 game text of one entry (skill | support | unique | keystone | notable | base), resolved exactly by name. `text`
    lines are what a slate claim may quote: copy the quote verbatim from one line. Also returns structure (skill types,
    support require/exclude/add types, unique base and slot). Unresolved names return suggestions."""
    return core.explain(kind, name)


@mcp.tool()
def diagnose(build: str, metric: str = "FullDPS", benchmarks: list[str] | None = None, top: int = 8) -> dict[str, Any]:
    """What limits this build? `build` = PoB build XML text. Applies ~17 calibrated probe levers (custom modifiers: more damage, crit,
    speed, skill level, penetration, added damage, life, ES, armour, evasion, resistances) and returns: constraints from the named
    benchmarks (e.g. ['arbiter_ash','breach_t15']; pressure = required/actual, > 1 violated), the BINDING constraint, levers ranked by
    shadow price (share of the binding constraint's pressure removed per gear-tier point), and probes that failed (excluded, never
    shown as zero: PoB did not parse the line, or it failed calibration). `notes` flag levers whose sign reverses or vanishes on this
    build. About 25 s with two benchmarks. A lever is a measurement, not a recommendation."""
    return core.diagnose(build, metric, benchmarks, top)


@mcp.tool()
def ceilings(build: str, metric: str = "FullDPS", ids: list[str] | None = None, required: float | None = None,
             lines: dict[str, str] | None = None) -> dict[str, Any]:
    """How much could mechanics PoB cannot time be worth to this build? `build` = PoB build XML text. For each registry entry
    (data/ceilings.yaml: charge income/retention/spenders, Seal frequency, Infusions, Companion and Remnant lines) returns floor (pure
    PoB, the rank key), ceiling (mechanic ON 100% of the time, from a PoB option or a parseable line) and headroom (ceiling / floor;
    `compounding` at or above 1.5). `required` = a metric value to reach (e.g. the runner-up's): the text states the uptime needed.
    `lines` = {id: the piece's stat line} to fill numbers. Status: native (PoB computes it already), derived (per-charge bonus read
    from PoB skill data, upper bound), inert (nothing in this build reads the state), no_model, no_own_damage, needs_data, dropped.
    No uptime is assumed and no ranked band is produced."""
    return core.ceilings(build, metric, ids, required, lines)


@mcp.tool()
def sweep(spec: str | dict[str, Any], kind: str, searched: bool = True, top: int = 20, workers: int | None = None,
          weapon: str | None = None) -> dict[str, Any]:
    """Engine sweep, background job (returns run_id; read with get_report): measure the change in the spec's metric from adding each
    catalogue entry of one kind, one at a time, on a probe seed built from the spec. kind: keystone | ascendancy (own ascendancy's
    notables) | support | unique:<slot> (slot as in preflight). searched=true (default) searches supports and the passive tree first,
    about 1-2 min in all; false is quicker but keystone deltas then include their path nodes. Flags: audit_outlier (check for an
    engine artefact), possibly_unmodelled (zero delta on an entry with text; PoB may not model it). Use for leads, at most two
    probe specs per slate; deltas are not finished-build numbers. weapon: catalogue weapon base (e.g. 'Crude Bow') put on the probe
    seed unmodded; REQUIRED to probe an attack main skill (the seed has no gear, so an attack skill does not evaluate), omit for spells."""
    return core.start_sweep(spec, kind, searched=searched, top=top, workers=workers, weapon=weapon)


@mcp.tool()
def validate_slate(slate: str | dict[str, Any]) -> dict[str, Any]:
    """Gate a slate of candidate builds (YAML text or object; schema in ideation_guide). Deterministic, no engine. Per candidate: kept
    or rejected with issues: every spec validates; key pieces (1-3) resolve exactly and are fixed in the spec; every claim cites
    PoE2 text and each quote is a substring of that entry's text; claims contain no numbers; the main skill has a metric;
    candidates differ enough (near_duplicate). Slate issues: too few candidates, coverage of deliveries/damage types, brief ids.
    Fix or replace rejected candidates and re-run; do not paraphrase quotes."""
    return core.validate_slate(slate)


@mcp.tool()
def preflight_slate(slate: str | dict[str, Any], bases: dict[str, str] | None = None, workers: int | None = None,
                    deepen_k: int | None = None) -> dict[str, Any]:
    """Validate a slate and estimate run_slate time (screen every kept candidate at one tier, ablate its key pieces, full run for
    the top deepen_k, default 3). bases = default gear slot -> base for candidates without their own `bases:`. Lists rejected
    candidates and any candidate with no bases. Give the user the estimate; over_cap means run_slate needs force."""
    return core.preflight_slate(slate, bases, workers, deepen_k)


@mcp.tool()
def run_slate(slate: str | dict[str, Any], bases: dict[str, str] | None = None, workers: int | None = None, deepen_k: int | None = None,
              max_minutes: float | None = None, force: bool = False, unarmed_ok: bool = False) -> dict[str, Any]:
    """Start a slate run in the background and return run_id: screen each kept candidate, ablate its key pieces (keystone/notable
    removed, support swapped for the next best, unique replaced by the best rare for its slot), rank on benchmark metrics only,
    then full runs for the top deepen_k at every brief tier. Validates first; refuses over the cap (default 45 min) unless force,
    set only after the user has seen the estimate. A candidate with no bases is refused unless unarmed_ok=true, which runs it with no
    searched gear (unarmed builds; values are the bare build). Poll run_status about once a minute; then get_report."""
    return core.start_slate(slate, bases, workers=workers, deepen_k=deepen_k, max_minutes=max_minutes, force=force, unarmed_ok=unarmed_ok)


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
