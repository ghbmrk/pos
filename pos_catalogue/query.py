"""Read-only catalogue queries for ideation (docs/ideation.md): search, enablers, bridges, explain. No engine needed."""
from __future__ import annotations

import re

# kinds with quotable game text
TEXT_KINDS = ("skill", "support", "unique", "keystone", "notable", "base")


def current_lines(u: dict) -> list[dict]:
    """A unique's mod lines for its newest variant (last `Variant:`); all lines if it has none."""
    vs = u.get("variants")
    if not vs:
        return list(u.get("lines", []))
    cur = len(vs)
    return [l for l in u.get("lines", []) if not l.get("variants") or cur in l["variants"]]


def texts(kind: str, e: dict) -> list[str]:
    """The entry's quotable PoE2 text, one string per line (what a claim may cite)."""
    if kind in ("keystone", "notable"):
        return list(e.get("stats") or [])
    if kind == "unique":
        return [l["text"] for l in current_lines(e)]
    if kind in ("skill", "support"):
        return [e["description"]] if e.get("description") else []
    if kind == "base":
        return [e["implicit"]] if e.get("implicit") else []
    raise ValueError(f"kind must be one of {TEXT_KINDS}")


def _words(term: str) -> re.Pattern:
    return re.compile(r"(?<![a-z0-9])" + re.escape(term.casefold().strip()))


def mentions(kind: str, e: dict, term: str) -> bool:
    """True if the term starts a word in the entry's name or text (so 'fire' matches 'Fireball', not 'Misfire')."""
    pat = _words(term)
    return any(pat.search(s.casefold()) for s in [e["name"], *texts(kind, e)])


def search(cat, kind: str, text: str | None = None, skill_types: list[str] | None = None, tags: list[str] | None = None,
           ascendancy: str | None = None, class_: str | None = None, limit: int | None = None) -> list[dict]:
    """Filter entries of one kind. All filters AND together; `text` terms (whitespace-separated) must each start a word in name or text.

    skill_types: skill/support entries having every type (support: in require_types/add_types/skill types).
    tags: gem tags (case-insensitive) or base tags. ascendancy: notables of that ascendancy. class_: ascendancies of that class.
    """
    out = []
    terms = (text or "").split()
    for e in cat.entries(kind):
        if terms and not all(mentions(kind, e, t) for t in terms):
            continue
        if skill_types:
            have = set(e.get("skill_types") or []) | set(e.get("require_types") or []) | set(e.get("add_types") or [])
            if not all(t in have for t in skill_types):
                continue
        if tags:
            raw = e.get("tags")
            have_t = {t.strip().casefold() for t in (raw.split(",") if isinstance(raw, str) else (raw or []))}
            if not all(t.casefold() in have_t for t in tags):
                continue
        if ascendancy is not None and (e.get("ascendancy") or "").casefold() != ascendancy.casefold():
            continue
        if class_ is not None and (e.get("class") or "").casefold() != class_.casefold():
            continue
        out.append(e)
        if limit and len(out) >= limit:
            break
    return out


def enablers(cat, skill_type: str) -> dict[str, list[dict]]:
    """What grants or names a skill type: supports whose add_types include it, and keystones/notables/uniques/skills whose text names it."""
    out = {"supports_adding": [e for e in cat.entries("support") if skill_type in (e.get("add_types") or [])]}
    for kind in ("keystone", "notable", "unique"):
        out[kind + "s"] = [e for e in cat.entries(kind) if any(_words(skill_type).search(s.casefold()) for s in texts(kind, e))]
    return out


def bridges(cat, term_a: str, term_b: str, limit: int | None = None) -> dict[str, list[dict]]:
    """Entries whose text (or name) mentions both terms, per kind. Co-occurrence of unrelated terms is where non-obvious combinations live."""
    out = {}
    for kind in ("keystone", "notable", "unique", "support", "skill"):
        hits = [e for e in cat.entries(kind) if mentions(kind, e, term_a) and mentions(kind, e, term_b)]
        out[kind + "s"] = hits[:limit] if limit else hits
    return out


def explain(cat, kind: str, id_: str) -> dict:
    """The full text the LLM may quote for an entry. Uniques with several bases return the first; use `base=` via the catalogue entry if needed."""
    e = cat.get(kind, id_)
    out = {"kind": kind, "id": id_, "name": e["name"], "text": texts(kind, e)}
    if kind == "unique":
        out.update(base=e["base"], slot=e["file"], variants=e.get("variants"),
                   implicit_count=sum(1 for l in current_lines(e) if l.get("implicit")),
                   all_lines=e.get("lines"))
    elif kind in ("skill", "support"):
        out.update({k: e.get(k) for k in ("tags", "skill_types", "require_types", "exclude_types", "add_types", "family") if e.get(k) is not None})
    elif kind in ("keystone", "notable"):
        out["ascendancy"] = e.get("ascendancy")
    return out
