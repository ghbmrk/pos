"""Meta lessons: abstract scaling patterns from past metas, used by ideation as priors (data/meta_lessons.yaml,
docs/meta-lessons.md). Owner requirement cmsg_01RxGYnd78N9kMbbAJ5pWDhUX2GMWf6TSLPYKzmKmpb39v.

Only abstract text and verified PoE2 catalogue names leave this module. `examples` (past-meta names, mostly PoE1) stay
in the YAML for provenance and are never rendered: they are the names the slate gate exists to catch."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from . import data

_RENDERED = ("principle", "compounds", "limits")
_SPLIT = re.compile(r"[+,\s]+")


@lru_cache(maxsize=None)
def load() -> dict:
    return data._load("meta_lessons.yaml")


def patterns() -> list[dict]:
    return load()["patterns"]


def ids() -> list[str]:
    return [p["id"] for p in patterns()]


def parse_ids(text: str) -> list[str]:
    """`archetype.patterns` is a string: ids joined by '+' or ','."""
    return [t for t in _SPLIT.split(text or "") if t]


def public(pattern_id: str | None = None) -> list[dict]:
    """Patterns without provenance examples (safe to hand to a client model)."""
    out = []
    for p in patterns():
        if pattern_id and p["id"] != pattern_id:
            continue
        q = {k: p[k] for k in ("id", "title", "side", *_RENDERED, "levers", "pob")}
        q["eras"] = [{k: e[k] for k in ("game", "era", "evidence")} for e in p.get("eras", [])]
        q["poe2"] = p.get("poe2", {})
        out.append(q)
    return out


def _anchor_names(p: dict) -> list[str]:
    return [a["name"] for a in (p.get("poe2") or {}).get("anchors", [])]


def side_of(pattern_id: str) -> str | None:
    return next((p.get("side") for p in patterns() if p["id"] == pattern_id), None)


def render(limit: int | None = None) -> str:
    """Compact prompt block: patterns with a PoE2 path in the pinned data, offence first, then defence."""
    lim = limit or load()["rules"]["max_rendered"]
    shown = [p for p in patterns() if not (p.get("poe2") or {}).get("absent")][:lim]
    out = []
    for head, sides in (("Offence (engine)", ("offence", "both")), ("Defence (layers)", ("defence", "both"))):
        out.append(f"{head}:")
        for p in shown:
            if p.get("side") not in sides or (head.startswith("Defence") and p.get("side") == "both"):
                continue
            anchors = ", ".join(_anchor_names(p))
            tag = " [offence and defence]" if p.get("side") == "both" else ""
            out.append(f"- `{p['id']}` {p['title']}{tag}. {p['principle']} Compounds: {p['compounds']} Limits: {p['limits']}"
                       f" PoE2 starting points: {anchors}.")
    return "\n".join(out)


def validate(cat=None, probes: dict | None = None) -> list[str]:
    """Problems in the corpus: anchors that do not resolve exactly, unknown probe levers, bad evidence, leaked
    example names in rendered text. Empty list = valid."""
    from pos_catalogue import Catalogue
    cat = cat or Catalogue.load()
    probes = probes if probes is not None else data._load("probes.yaml")
    probe_ids = {p["id"] for p in probes.get("probes", [])}
    root = Path(data.DATA).parent
    problems: list[str] = []
    seen: set[str] = set()
    examples: set[str] = set()
    for p in patterns():
        for e in p.get("eras", []):
            examples.update(x for x in e.get("examples", []))
    for p in patterns():
        pid = p.get("id", "?")
        if pid in seen:
            problems.append(f"{pid}: duplicate id")
        seen.add(pid)
        if p.get("side") not in ("offence", "defence", "both"):
            problems.append(f"{pid}: side must be offence | defence | both")
        for k in ("title", *_RENDERED, "eras", "poe2", "levers", "pob"):
            if k not in p:
                problems.append(f"{pid}: missing {k}")
        if p.get("pob") not in ("modelled", "partial", "not_modelled"):
            problems.append(f"{pid}: pob must be modelled | partial | not_modelled")
        for e in p.get("eras", []):
            ev = str(e.get("evidence", ""))
            if ev != "recall" and not (ev.startswith("snapshot:") and (root / ev[len("snapshot:"):]).is_file()):
                problems.append(f"{pid}: evidence {ev!r} is neither 'recall' nor snapshot:<existing file>")
            if e.get("game") not in ("poe1", "poe2"):
                problems.append(f"{pid}: era game must be poe1 | poe2")
        poe2 = p.get("poe2") or {}
        if not poe2.get("absent") and not poe2.get("anchors"):
            problems.append(f"{pid}: no PoE2 anchors (set poe2.absent: true if the pinned data has none)")
        for a in poe2.get("anchors", []):
            r = cat.resolve(a["kind"], a["name"])
            if r.status != "exact":
                problems.append(f"{pid}: anchor {a['kind']} {a['name']!r} is {r.status} in {cat.pob_sha[:7]}"
                                f" (suggestions: {[e.get('name') for e in r.suggestions][:3]})")
        for lv in p.get("levers", []):
            if lv not in probe_ids:
                problems.append(f"{pid}: lever {lv!r} not in data/probes.yaml")
        anchors = {n.casefold() for n in _anchor_names(p)}
        text = " ".join(str(p.get(k, "")) for k in ("title", *_RENDERED)).casefold()
        for x in examples:
            # an example name may appear in rendered text only if it is also a verified PoE2 anchor of some pattern
            if re.search(rf"\b{re.escape(x.casefold())}\b", text) and x.casefold() not in anchors and not _is_anchor_anywhere(x):
                problems.append(f"{pid}: rendered text names past-meta example {x!r}")
    return problems


def _is_anchor_anywhere(name: str) -> bool:
    n = name.casefold()
    return any(n == a.casefold() for p in patterns() for a in _anchor_names(p))
