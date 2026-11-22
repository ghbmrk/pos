"""MCP server (stdio). `python -m pos_mcp`. Tool descriptions are the contract the LLM client reads: keep them exact."""
from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from . import core

INSTRUCTIONS = """Path of Sim: test PoE2 build ideas with real Path of Building calculations at gear price tiers.
Workflow: (1) turn the user's idea into a build spec; every name (class, ascendancy, skill, support, unique, base,
keystone, notable) MUST come from `resolve` - never type a game name from memory. (2) `validate_spec` until ok.
(3) `preflight` and tell the user the estimated time; (4) `run` with a base per gear slot; (5) poll `run_status`;
(6) `get_report` and summarise. Quote numbers only from the report; do not estimate DPS, EHP or prices yourself.
Read the report's limitations and any 'unsourced'/incomplete flags aloud rather than smoothing them over."""

mcp = MCPServer("path-of-sim", instructions=INSTRUCTIONS)


@mcp.tool()
def resolve(kind: str, names: list[str], pob_sha: str | None = None) -> dict[str, Any]:
    """Look up game names in the pinned PoE2 catalogue. kind: class | ascendancy | skill | support | unique | base | keystone | notable.
    Per name returns status exact | ambiguous | unresolved plus near-match suggestions. Never guesses: use only exact matches
    (ask the user to choose between ambiguous or suggested ones). Run this before putting any name in a spec."""
    return core.resolve(kind, names, pob_sha)


@mcp.tool()
def validate_spec(spec: str | dict[str, Any]) -> dict[str, Any]:
    """Validate a build spec (YAML text or object; schema in docs/spec.md) against the catalogue and the engine's known limits.
    Returns ok, the metric the run will rank by, and issues (error/warning with code and suggestions). Fix every error before `run`;
    report warnings and 'limitation' issues to the user. Required keys: pob_sha, class, level, main_skill {gem}, tiers (e.g. [starter, mid]).
    Optional: ascendancy, fixed {supports,keystones,notables,uniques}, axes (name -> values to vary), objective, benchmarks."""
    return core.validate_spec(spec)


@mcp.tool()
def import_pob(code: str) -> dict[str, Any]:
    """Convert a Path of Building share code (or build XML) into a draft spec plus warnings for anything dropped. Edit the draft, then validate_spec."""
    return core.import_pob(code)


@mcp.tool()
def preflight(spec: str | dict[str, Any], bases: dict[str, str] | None = None, workers: int | None = None,
              realloc_rounds: int | None = None) -> dict[str, Any]:
    """Estimate wall time without running (also validates). bases maps gear slot -> base item name, e.g. {"weapon": "Acrid Wand", "ring": "Iron Ring"}
    (slots: weapon, body, amulet, ring_1, ring_2, helmet, gloves, boots, belt; `ring` sets both). More slots, seeds (axes) and tiers cost more.
    over_cap=true means the run will be refused unless forced: tell the user the estimate and let them decide."""
    return core.preflight(spec, bases, workers, realloc_rounds)


@mcp.tool()
def run(spec: str | dict[str, Any], bases: dict[str, str], workers: int | None = None, realloc_rounds: int | None = None,
        max_minutes: float | None = None, force: bool = False) -> dict[str, Any]:
    """Start a run in the background and return a run_id at once (minutes to tens of minutes). Validates first and refuses an invalid spec or an
    estimate above the cap (default 45 min) unless force=true - set force only after the user has seen the estimate. realloc_rounds=0 is a
    cheaper, weaker gear search. One run at a time. Poll run_status."""
    return core.start_run(spec, bases, workers=workers, realloc_rounds=realloc_rounds, max_minutes=max_minutes, force=force)


@mcp.tool()
def run_status(run_id: str) -> dict[str, Any]:
    """State of a run: running | done | failed | cancelled, elapsed seconds, and the last log lines. Poll sparingly (every minute or more)."""
    return core.run_status(run_id)


@mcp.tool()
def cancel_run(run_id: str) -> dict[str, Any]:
    """Stop a running run."""
    return core.cancel_run(run_id)


@mcp.tool()
def get_report(run_id: str, max_chars: int = 20000) -> dict[str, Any]:
    """The finished run's ranked report (markdown): per tier the best variants with DPS/EHP/resists, gear, supports, benchmark results,
    price labels and limitation notes; and which axis value wins at which budget. These numbers are the only ones to quote."""
    return core.get_report(run_id, max_chars)


@mcp.tool()
def compare(run_a: str, run_b: str) -> dict[str, Any]:
    """Best result per tier in two finished runs and the % delta (same metric only)."""
    return core.compare(run_a, run_b)


@mcp.tool()
def list_runs(limit: int = 10) -> dict[str, Any]:
    """Recent run ids and states."""
    return core.list_runs(limit)


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
