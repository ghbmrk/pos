"""Re-validate saved specs against a new catalogue. Specs are never edited; failures carry the validator's suggestions."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path

from pos_catalogue import Catalogue
from pos_pipeline import SpecError, load_spec, validate


@dataclass
class SpecResult:
    path: str
    old_sha: str | None
    ok: bool
    errors: list[str]
    warnings: list[str]


def find_specs(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(p for ext in ("*.yaml", "*.yml") for p in root.rglob(ext)) if root.exists() else []


def revalidate_specs(root: Path, cat: Catalogue) -> list[SpecResult]:
    """The spec's recorded pob_sha is replaced by the new pin before validating, so only content problems are reported."""
    out = []
    for p in find_specs(root):
        try:
            spec = load_spec(p)
        except SpecError as e:
            out.append(SpecResult(str(p), None, False, [f"spec: {e}"], []))
            continue
        rep = validate(dataclasses.replace(spec, pob_sha=cat.pob_sha[:7]), cat)
        fmt = lambda i: f"{i.code} {i.path}: {i.message}" + (f" [suggestions: {', '.join(i.suggestions)}]" if i.suggestions else "")  # noqa: E731
        out.append(SpecResult(str(p), spec.pob_sha, rep.ok, [fmt(i) for i in rep.errors], [fmt(i) for i in rep.warnings]))
    return out


def render(results: list[SpecResult], root: Path) -> str:
    bad = [r for r in results if not r.ok]
    out = ["## Spec revalidation", "", f"{len(results)} spec(s) under `{root}`; {len(bad)} fail against the new catalogue."]
    if not results:
        out.append("No saved specs found (nothing to migrate).")
    for r in results:
        out += ["", f"- `{r.path}` (was pinned to {r.old_sha}): " + ("ok" if r.ok else "FAIL")]
        out += [f"  - error: {e}" for e in r.errors] + [f"  - warning: {w}" for w in r.warnings]
    out += ["", "Specs are not rewritten. After fixing, set `pob_sha` to the new pin; old results stay reproducible against their own pin."]
    return "\n".join(out) + "\n"
