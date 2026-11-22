"""Load a catalogue and resolve free-text names to ids, with suggestions instead of silent repair."""
from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .export import CATALOGUE_DIR

# kind -> (catalogue key, id field, label field)
_KINDS = {
    "class": ("classes", "name"),
    "ascendancy": ("ascendancies", "name"),
    "skill": ("skills", "id"),
    "support": ("supports", "id"),
    "unique": ("uniques", "name"),
    "base": ("bases", "name"),
    "keystone": ("keystones", "name"),
    "notable": ("notables", "name"),
}
KINDS = tuple(_KINDS)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", s.casefold().replace("'s ", "s ").replace("-", " ")).strip()


@dataclass
class Resolution:
    kind: str
    query: str
    status: str  # exact | ambiguous | unresolved
    matches: list[dict] = field(default_factory=list)      # entries whose name equals the query (normalised)
    suggestions: list[dict] = field(default_factory=list)  # near matches, best first (empty when exact)

    @property
    def entry(self) -> dict | None:
        return self.matches[0] if self.status == "exact" else None



def _eval(expr: list[str] | None, have: set[str]) -> bool:
    """PoB's postfix type expression: bare names push membership, OR/AND/NOT combine; true if any stack entry is true."""
    stack: list[bool] = []
    for tok in expr or []:
        if tok == "OR" and len(stack) >= 2:
            b, a = stack.pop(), stack.pop(); stack.append(a or b)
        elif tok == "AND" and len(stack) >= 2:
            b, a = stack.pop(), stack.pop(); stack.append(a and b)
        elif tok == "NOT" and stack:
            stack.append(not stack.pop())
        elif tok not in ("OR", "AND", "NOT"):
            stack.append(tok in have)
    return any(stack)


def can_support(support: dict, skill: dict) -> bool:
    """True if `support` may support `skill` by skill types (PoB's require/exclude rule).

    Does not model supports that add types to each other, minion-only rules, or socket limits.
    """
    have = set(skill.get("skill_types") or [])
    if support.get("require_types") and not _eval(support["require_types"], have):
        return False
    if support.get("exclude_types") and _eval(support["exclude_types"], have):
        return False
    return True


class Catalogue:
    def __init__(self, data: dict):
        self.data = data
        self.pob_sha: str = data["pob_sha"]
        self._index: dict[str, list[tuple[str, dict]]] = {}
        for kind, (key, _) in _KINDS.items():
            self._index[kind] = [(_norm(e["name"]), e) for e in data[key]]

    @classmethod
    def load(cls, path: Path | str | None = None, pob_sha: str | None = None) -> "Catalogue":
        if path is None:
            files = sorted(CATALOGUE_DIR.glob("*.json"))
            if pob_sha:
                files = [f for f in files if f.stem == pob_sha[:7]]
            if not files:
                raise FileNotFoundError("no catalogue in data/catalogue; run `python -m pos_catalogue export`")
            if len(files) > 1 and not pob_sha:
                try:  # after a re-pin several exist; default to the pinned PoB's
                    from .export import pob_sha as pinned
                    files = [f for f in files if f.stem == pinned()[:7]] or files
                except Exception:
                    pass
            if len(files) > 1:
                raise ValueError(f"several catalogues, pass pob_sha: {[f.stem for f in files]}")
            path = files[0]
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def entries(self, kind: str) -> list[dict]:
        return self.data[_KINDS[kind][0]]

    def get(self, kind: str, id_: str) -> dict:
        idf = _KINDS[kind][1]
        for e in self.entries(kind):
            if e[idf] == id_:
                return e
        raise KeyError(f"{kind} {id_!r} not in catalogue {self.pob_sha[:7]}")

    def resolve(self, kind: str, text: str, limit: int = 5) -> Resolution:
        """Exact (case/punctuation-insensitive) name match, else ranked suggestions. Never guesses."""
        if kind not in _KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        q = _norm(text)
        idx = self._index[kind]
        matches = [e for n, e in idx if n == q] if q else []
        if matches:
            return Resolution(kind, text, "exact" if len(matches) == 1 else "ambiguous", matches)
        names = {}
        for n, e in idx:
            names.setdefault(n, []).append(e)
        scored: dict[str, float] = {}
        for n in names:
            if q and (q in n or n in q):
                scored[n] = max(scored.get(n, 0), 0.9)
            r = difflib.SequenceMatcher(None, q, n).ratio()
            if r >= 0.6:
                scored[n] = max(scored.get(n, 0), r)
        suggestions: list[dict] = []
        for n in sorted(scored, key=lambda n: (-scored[n], n)):
            suggestions.extend(names[n])
            if len(suggestions) >= limit:
                break
        return Resolution(kind, text, "unresolved", [], suggestions[:limit])

    def supporting(self, skill_id: str) -> list[dict]:
        """Support gems whose type requirements the skill meets."""
        skill = self.get("skill", skill_id)
        return [s for s in self.data["supports"] if can_support(s, skill)]

    # read-only ideation queries (see query.py)
    def search(self, kind: str, **kw) -> list[dict]:
        from . import query
        return query.search(self, kind, **kw)

    def enablers(self, skill_type: str) -> dict:
        from . import query
        return query.enablers(self, skill_type)

    def bridges(self, term_a: str, term_b: str, limit: int | None = None) -> dict:
        from . import query
        return query.bridges(self, term_a, term_b, limit)

    def explain(self, kind: str, id_: str) -> dict:
        from . import query
        return query.explain(self, kind, id_)
