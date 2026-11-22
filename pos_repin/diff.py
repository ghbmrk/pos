"""Diff two catalogues: added, removed, renamed (same key, new name) and changed entries per kind."""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field

# catalogue key -> fields forming the stable key; label is always "name".
KEYS = {
    "skills": ("id",),
    "supports": ("id",),
    "uniques": ("name", "base"),
    "bases": ("name",),
    "classes": ("name",),
    "ascendancies": ("name",),
    "keystones": ("node",),
    "notables": ("node",),
}
# Kinds whose key includes the name: a rename shows up as removed + added, so pair them by similarity.
NAME_KEYED = {"uniques", "bases", "classes", "ascendancies"}
SIMILAR = 0.8


@dataclass
class KindDiff:
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    renamed: list[tuple[str, str]] = field(default_factory=list)       # certain: same key, name changed
    possible_renamed: list[tuple[str, str]] = field(default_factory=list)  # removed+added with similar names
    changed: list[tuple[str, list[str]]] = field(default_factory=list)  # (label, changed fields)

    @property
    def empty(self) -> bool:
        return not (self.added or self.removed or self.renamed or self.possible_renamed or self.changed)


@dataclass
class CatalogueDiff:
    old_sha: str
    new_sha: str
    tree_version: tuple[str, str]
    kinds: dict[str, KindDiff]

    @property
    def breaking(self) -> int:
        """Entries a saved spec could name that are gone or renamed."""
        return sum(len(k.removed) + len(k.renamed) + len(k.possible_renamed) for k in self.kinds.values())


def _sim(a: str, b: str) -> float:
    a, b = a.casefold(), b.casefold()
    return 1.0 if (a in b or b in a) else difflib.SequenceMatcher(None, a, b).ratio()


def _key(kind: str, e: dict) -> tuple:
    return tuple(e.get(f) for f in KEYS[kind])


def _label(kind: str, e: dict) -> str:
    extra = f" ({e['base']})" if kind == "uniques" and e.get("base") else ""
    return f"{e['name']}{extra}"


def _diff_kind(kind: str, old: list[dict], new: list[dict]) -> KindDiff:
    o = {_key(kind, e): e for e in old}
    n = {_key(kind, e): e for e in new}
    d = KindDiff()
    for k in sorted(o.keys() & n.keys(), key=str):
        a, b = o[k], n[k]
        if a == b:
            continue
        if a.get("name") != b.get("name"):
            d.renamed.append((_label(kind, a), _label(kind, b)))
        fields = sorted(f for f in (a.keys() | b.keys()) if f != "name" and a.get(f) != b.get(f))
        if fields:
            d.changed.append((_label(kind, b), fields))
    removed = [o[k] for k in sorted(o.keys() - n.keys(), key=str)]
    added = [n[k] for k in sorted(n.keys() - o.keys(), key=str)]
    if kind in NAME_KEYED:
        free = list(added)
        for r in list(removed):
            best = max(free, key=lambda x: _sim(r["name"], x["name"]), default=None)
            if best and _sim(r["name"], best["name"]) >= SIMILAR and r.get("base") == best.get("base"):
                d.possible_renamed.append((_label(kind, r), _label(kind, best)))
                removed.remove(r); free.remove(best); added.remove(best)
    d.removed = [_label(kind, e) for e in removed]
    d.added = [_label(kind, e) for e in added]
    return d


def diff_catalogues(old: dict, new: dict) -> CatalogueDiff:
    kinds = {k: _diff_kind(k, old[k], new[k]) for k in KEYS}
    return CatalogueDiff(old["pob_sha"], new["pob_sha"], (old.get("tree_version", "?"), new.get("tree_version", "?")), kinds)


def render(d: CatalogueDiff, limit: int = 40) -> str:
    out = [f"## Catalogue diff {d.old_sha[:7]} -> {d.new_sha[:7]}", "",
           f"Tree version: {d.tree_version[0]} -> {d.tree_version[1]}" + ("" if d.tree_version[0] == d.tree_version[1] else " (CHANGED)"),
           f"Entries a saved spec could name that are removed or renamed: {d.breaking}", ""]
    out += ["| kind | added | removed | renamed | possibly renamed | changed |", "|---|---|---|---|---|---|"]
    for k, kd in d.kinds.items():
        out.append(f"| {k} | {len(kd.added)} | {len(kd.removed)} | {len(kd.renamed)} | {len(kd.possible_renamed)} | {len(kd.changed)} |")
    for k, kd in d.kinds.items():
        if kd.empty:
            continue
        out += ["", f"### {k}"]
        def lst(title, items, fmt):
            if items:
                out.append(f"**{title}** ({len(items)})")
                out.extend(f"- {fmt(i)}" for i in items[:limit])
                if len(items) > limit:
                    out.append(f"- ... {len(items) - limit} more")
        lst("removed", kd.removed, str)
        lst("renamed", kd.renamed, lambda p: f"{p[0]} -> {p[1]}")
        lst("possibly renamed (similar name, same base; unconfirmed)", kd.possible_renamed, lambda p: f"{p[0]} -> {p[1]}")
        lst("added", kd.added, str)
        lst("changed fields", kd.changed, lambda p: f"{p[0]}: {', '.join(p[1])}")
    return "\n".join(out) + "\n"
