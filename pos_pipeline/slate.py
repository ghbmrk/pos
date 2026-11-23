"""Idea slate: schema + deterministic gate `validate_slate` (docs/ideation.md, I3). No engine, no LLM.

Each candidate is a BuildSpec plus archetype, key pieces and mechanism claims. A candidate is kept only if its spec
validates, every name resolves exactly in the pinned catalogue, every claim quotes PoE2 catalogue text (and states no
number), key pieces are in the spec, its skill has a metric, and it is not a near-duplicate of an earlier kept one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import yaml

from pos_catalogue import Catalogue
from pos_catalogue.query import texts
from pos_tiers.tiers import TierTable

from . import data
from .benchmarks import benchmarks as _benchmarks
from .spec import BuildSpec, SpecError, parse_spec
from .validate import Issue, _lookup, validate

ARCH_FIELDS = ("class_asc", "delivery", "damage", "defence", "main_skill", "key_pieces")
_TOP = {"slate", "pob_sha", "prompt", "brief", "candidates"}
_BRIEF = {"benchmarks", "tiers", "constraints", "floors"}
_CAND = {"name", "archetype", "spec", "key_pieces", "claims", "source", "bases"}
_ARCH = {"delivery", "damage", "defence", "engine", "patterns"}   # patterns: meta-lesson ids joined by "+"
_SOURCE = re.compile(r"^(llm|sweep:[^/\s]+/\S.*)$")


class SlateError(SpecError):
    """Structural problem in the slate file (wrong type, unknown key)."""


@dataclass
class Claim:
    text: str
    cites: list[dict]            # [{kind, id, quote}]


@dataclass
class Candidate:
    name: str
    spec: BuildSpec | None       # None if the spec block failed structural parsing
    spec_error: str | None
    archetype: dict[str, str]
    key_pieces: list[dict]       # [{kind, id}]
    claims: list[Claim]
    source: str
    bases: dict[str, str] = field(default_factory=dict)   # slot -> catalogue base for the gear search (I5); CLI bases fill the rest


@dataclass
class Slate:
    pob_sha: str
    prompt: str
    brief: dict
    candidates: list[Candidate]


@dataclass
class CandidateResult:
    name: str
    issues: list[Issue] = field(default_factory=list)
    kept: bool = False
    vector: dict[str, str] = field(default_factory=dict)   # derived archetype vector (diversity input)
    metric: str | None = None

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]


@dataclass
class SlateReport:
    issues: list[Issue] = field(default_factory=list)       # slate-level
    candidates: list[CandidateResult] = field(default_factory=list)

    @property
    def kept(self) -> list[CandidateResult]:
        return [c for c in self.candidates if c.kept]

    @property
    def ok(self) -> bool:
        return bool(self.kept) and not any(i.severity == "error" for i in self.issues)


# ---------------------------------------------------------------- schema

def _only(d: Any, allowed: set[str], where: str) -> dict:
    if not isinstance(d, dict):
        raise SlateError(f"{where} must be a mapping")
    extra = set(d) - allowed
    if extra:
        raise SlateError(f"{where}: unknown key(s) {sorted(extra)}; allowed {sorted(allowed)}")
    return d


def _ref_list(v: Any, where: str, keys: tuple[str, ...]) -> list[dict]:
    if not isinstance(v, list):
        raise SlateError(f"{where} must be a list")
    out = []
    for i, x in enumerate(v):
        _only(x, set(keys), f"{where}[{i}]")
        for k in keys:
            if not isinstance(x.get(k), str) or not x[k].strip():
                raise SlateError(f"{where}[{i}].{k} must be a non-empty string")
        out.append(dict(x))
    return out


def _bases(v: Any, where: str) -> dict[str, str]:
    if v is None:
        return {}
    if not isinstance(v, dict) or not all(isinstance(k, str) and isinstance(b, str) and b for k, b in v.items()):
        raise SlateError(f"{where}.bases must map slot names to base names")
    return dict(v)


def parse_slate(d: Any) -> Slate:
    d = _only(d, _TOP, "slate")
    if d.get("slate") != 1:
        raise SlateError("slate: schema version must be `slate: 1`")
    for req in ("pob_sha", "prompt", "brief", "candidates"):
        if req not in d:
            raise SlateError(f"slate: missing required key {req!r}")
    if not isinstance(d["pob_sha"], str) or not d["pob_sha"]:
        raise SlateError("pob_sha must be a string (quote hex)")
    if not isinstance(d["prompt"], str):
        raise SlateError("prompt must be a string")
    brief = _only(d["brief"], _BRIEF, "brief")
    for k in ("benchmarks", "tiers"):
        v = brief.get(k, [])
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise SlateError(f"brief.{k} must be a list of strings")
    for k in ("constraints", "floors"):
        if not isinstance(brief.get(k, {}), dict):
            raise SlateError(f"brief.{k} must be a mapping")
    if not isinstance(d["candidates"], list):
        raise SlateError("candidates must be a list")
    cands = []
    for i, c in enumerate(d["candidates"]):
        w = f"candidates[{i}]"
        c = _only(c, _CAND, w)
        for req in ("name", "spec", "key_pieces", "claims"):
            if req not in c:
                raise SlateError(f"{w}: missing required key {req!r}")
        if not isinstance(c["name"], str) or not c["name"].strip():
            raise SlateError(f"{w}.name must be a non-empty string")
        arch = _only(c.get("archetype") or {}, _ARCH, f"{w}.archetype")
        if not all(isinstance(v, str) for v in arch.values()):
            raise SlateError(f"{w}.archetype values must be strings")
        claims = []
        if not isinstance(c["claims"], list):
            raise SlateError(f"{w}.claims must be a list")
        for j, cl in enumerate(c["claims"]):
            cl = _only(cl, {"text", "cites"}, f"{w}.claims[{j}]")
            if not isinstance(cl.get("text"), str) or not cl["text"].strip():
                raise SlateError(f"{w}.claims[{j}].text must be a non-empty string")
            claims.append(Claim(cl["text"], _ref_list(cl.get("cites", []), f"{w}.claims[{j}].cites", ("kind", "id", "quote"))))
        try:
            spec, serr = parse_spec(c["spec"]), None
        except SpecError as e:
            spec, serr = None, str(e)
        cands.append(Candidate(c["name"].strip(), spec, serr, dict(arch), _ref_list(c["key_pieces"], f"{w}.key_pieces", ("kind", "id")),
                               claims, c.get("source", "llm"), _bases(c.get("bases"), w)))
    return Slate(d["pob_sha"], d["prompt"], dict(brief), cands)


def load_slate(path) -> Slate:
    from pathlib import Path
    return parse_slate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


# ---------------------------------------------------------------- helpers

def _norm(s: str) -> str:
    return " ".join(s.casefold().split())


def _has_number(text: str, words: list[str]) -> str | None:
    m = re.search(r"\d|%", text)
    if m:
        return m.group(0)
    toks = set(re.findall(r"[a-z]+", text.casefold()))
    hit = sorted(toks & set(words))
    return hit[0] if hit else None


def _derive_delivery(cfg: dict, skill: dict | None, support_entries: list[dict]) -> str:
    for e in support_entries:
        for t, label in cfg["delivery_support_requires"].items():
            if t in (e.get("require_types") or []):
                return label
    have = set((skill or {}).get("skill_types") or [])
    for r in cfg["delivery"]:
        if not r["any"] or have & set(r["any"]):
            return r["label"]
    return "other"


def _derive_damage(cfg: dict, skill: dict | None) -> str:
    have = set((skill or {}).get("skill_types") or [])
    el = sorted(t for t in cfg["damage"] if t in have)
    return "+".join(el) if el else "unknown"


# ---------------------------------------------------------------- gate

def validate_slate(slate: Slate, cat: Catalogue, tiers: TierTable | None = None) -> SlateReport:
    cfg = data.ideation()
    rep = SlateReport()
    sadd = lambda sev, code, path, msg, sug=(): rep.issues.append(Issue(sev, code, path, msg, list(sug)))  # noqa: E731
    tiers = tiers or TierTable.load()

    if not cat.pob_sha.startswith(slate.pob_sha) or len(slate.pob_sha) < 7:
        sadd("error", "pob_sha", "pob_sha", f"slate pinned to {slate.pob_sha!r} but catalogue is {cat.pob_sha[:7]}")
    _check_brief(slate.brief, tiers, sadd)
    if len(slate.candidates) < cfg["slate"]["min_candidates"]:
        sadd("error", "too_few", "candidates", f"{len(slate.candidates)} candidates; at least {cfg['slate']['min_candidates']} required")
    seen_names: dict[str, int] = {}
    for i, c in enumerate(slate.candidates):
        if _norm(c.name) in seen_names:
            sadd("error", "duplicate", f"candidates[{i}].name", f"name {c.name!r} already used by candidates[{seen_names[_norm(c.name)]}]")
        seen_names.setdefault(_norm(c.name), i)

    for i, c in enumerate(slate.candidates):
        rep.candidates.append(_check_candidate(i, c, cat, tiers, cfg))

    _diversity(slate, rep, cfg)
    return rep


def _check_brief(brief: dict, tiers: TierTable, sadd) -> None:
    known_b = set(_benchmarks())
    for i, b in enumerate(brief.get("benchmarks", [])):
        if b not in known_b:
            sadd("error", "benchmark", f"brief.benchmarks[{i}]", f"unknown benchmark {b!r}", sorted(known_b))
    for i, t in enumerate(brief.get("tiers", [])):
        if t not in tiers.tier_names:
            sadd("error", "tier", f"brief.tiers[{i}]", f"unknown tier {t!r}", tiers.tier_names)
    if not brief.get("benchmarks"):
        sadd("error", "benchmark", "brief.benchmarks", "at least one benchmark required: cross-archetype ranking uses benchmark metrics only")
    if not brief.get("tiers"):
        sadd("error", "tier", "brief.tiers", "at least one tier required", tiers.tier_names)


def _check_candidate(i: int, c: Candidate, cat: Catalogue, tiers: TierTable, cfg: dict) -> CandidateResult:
    res = CandidateResult(c.name)
    p = f"candidates[{i}]"
    add = lambda sev, code, path, msg, sug=(): res.issues.append(Issue(sev, code, f"{p}.{path}", msg, list(sug)))  # noqa: E731

    if not _SOURCE.match(c.source):
        add("error", "source", "source", f"source {c.source!r} must be 'llm' or 'sweep:<probe>/<entry>'")

    # spec
    skill = None
    sup_entries: list[dict] = []
    if c.spec is None:
        add("error", "spec_structure", "spec", c.spec_error or "spec failed to parse")
    else:
        if c.spec.companion is not None and c.spec.companion.assumed is not None:
            add("error", "assumed_in_slate", "spec.companion.assumed",
                "assumed-Squire what-if specs stay out of ranked slates (their numbers rest on assumptions); run them singly with `run --assumed`")
        sr = validate(c.spec, cat, tiers)
        res.issues += [Issue(x.severity, x.code, f"{p}.spec.{x.path}", x.message, x.suggestions, x.confidence) for x in sr.issues]
        skill = _lookup(cat, "skill", c.spec.main_skill)[0]
        sup_entries = [e for e in (_lookup(cat, "support", s)[0] for s in c.spec.supports) if e]
        # rankability: the skill must have an engine metric (a named maximise does not make cross-archetype ranking possible)
        if skill:
            m = data.metric_for(skill.get("skill_types") or [])
            res.metric = m["metric"]
            if m["metric"] is None and not any(x.code == "no_metric" for x in sr.issues):
                add("error", "no_metric", "spec.main_skill", f"{skill['name']} has no engine metric ({m['note']}); not rankable yet")
        _check_brief_fit(c, add)

    # bases for the gear search: slot names and catalogue bases must exist
    from .gear import SLOTS
    for k, b in c.bases.items():
        if k not in SLOTS:
            add("error", "bases", f"bases.{k}", f"unknown slot {k!r}; one of {', '.join(SLOTS)}")
        elif _lookup(cat, "base", b)[0] is None:
            add("error", "unresolved", f"bases.{k}", f"base {b!r} not found in the catalogue")

    # key pieces
    kp = cfg["slate"]["key_pieces"]
    if not kp["min"] <= len(c.key_pieces) <= kp["max"]:
        add("error", "key_pieces", "key_pieces", f"{len(c.key_pieces)} key pieces; need {kp['min']}-{kp['max']}")
    kp_ids: list[str] = []
    for j, k in enumerate(c.key_pieces):
        e = _resolve_ref(cat, k["kind"], k["id"], f"key_pieces[{j}]", add, cfg["key_piece_kinds"])
        if e is None:
            continue
        kp_ids.append(f"{k['kind']}:{e['name']}")
        if c.spec is not None and not _in_spec(c.spec, cat, k["kind"], e):
            add("error", "key_piece_not_in_spec", f"key_pieces[{j}]", f"{k['kind']} {e['name']!r} is not fixed in the candidate's spec; "
                "ablation removes only what the spec fixes")
    if len(set(kp_ids)) != len(kp_ids):
        add("error", "duplicate", "key_pieces", "key piece listed twice")

    # claims
    if len(c.claims) < cfg["slate"]["claims"]["min"]:
        add("error", "claims", "claims", f"at least {cfg['slate']['claims']['min']} mechanism claim required")
    for j, cl in enumerate(c.claims):
        _check_claim(cl, f"claims[{j}]", cat, cfg, add)

    # meta-lesson patterns (data/meta_lessons.yaml): unknown ids are errors; fewer than the minimum is a warning,
    # because a label does not prove compounding (the engine measures that)
    from . import meta_lessons
    known_p = meta_lessons.ids()
    named = meta_lessons.parse_ids(c.archetype.get("patterns", ""))
    for pid in named:
        if pid not in known_p:
            add("error", "unknown_pattern", "archetype.patterns", f"unknown meta-lesson pattern {pid!r}", known_p)
    rules = meta_lessons.load()["rules"]
    sides = {pid: meta_lessons.side_of(pid) for pid in set(named) if pid in known_p}
    off = [pid for pid, sd in sides.items() if sd in ("offence", "both")]
    dfn = [pid for pid, sd in sides.items() if sd in ("defence", "both")]
    if len(off) < rules["min_patterns_per_engine"]:
        add("warning", "engine_not_compounding", "archetype.patterns",
            f"name the {rules['min_patterns_per_engine']}+ offence patterns this engine combines (meta_lessons); one pattern plus marginal gains rarely competes")
    if len(dfn) < rules["min_defence_layers"]:
        add("warning", "defence_not_layered", "archetype.patterns",
            f"name the {rules['min_defence_layers']}+ independent defence layers this build stacks (meta_lessons, side defence); one deep layer dies to what it does not cover")

    # archetype (derived where possible)
    delivery = _derive_delivery(cfg, skill, sup_entries)
    damage = _derive_damage(cfg, skill)
    for k, derived in (("delivery", delivery), ("damage", damage)):
        typed = c.archetype.get(k)
        if typed and _norm(typed) != _norm(derived):
            add("warning", "archetype_derived", f"archetype.{k}",
                f"declared {typed!r} but the main skill's catalogue types give {derived!r}; the derived value is used")
    spec = c.spec
    res.vector = {
        "class_asc": _norm((spec.ascendancy or spec.class_) if spec else ""),
        "delivery": delivery, "damage": damage,
        "defence": _norm(c.archetype.get("defence", "")) or "unspecified",
        "main_skill": _norm(skill["name"] if skill else (spec.main_skill if spec else "")),
        "key_pieces": ",".join(sorted(kp_ids)),
    }
    return res


def _check_brief_fit(c: Candidate, add) -> None:
    sp = c.spec
    # nothing structural to enforce beyond tiers/benchmarks validated by validate(); benchmarks listed in the spec must exist
    for b in sp.benchmarks:
        if b not in _benchmarks():
            add("error", "benchmark", "spec.benchmarks", f"unknown benchmark {b!r}", sorted(_benchmarks()))


def _resolve_ref(cat: Catalogue, kind: str, text: str, path: str, add, allowed: list[str]) -> dict | None:
    if kind not in allowed:
        add("error", "kind", f"{path}.kind", f"kind {kind!r} not allowed here", allowed)
        return None
    entry, r = _lookup(cat, kind, text)
    if entry is None:
        if r.status == "ambiguous":
            add("error", "ambiguous", f"{path}.id", f"{kind} {text!r} matches several entries; pick one",
                [f"{m['name']} ({m.get('base', m.get('id', ''))})" for m in r.matches])
        else:
            add("error", "unresolved", f"{path}.id", f"{kind} {text!r} not in catalogue {cat.pob_sha[:7]} (PoE1-only name?)",
                [s["name"] for s in r.suggestions])
    return entry


def _in_spec(spec: BuildSpec, cat: Catalogue, kind: str, e: dict) -> bool:
    listed = {"keystone": spec.keystones, "notable": spec.notables, "unique": spec.uniques, "support": spec.supports}[kind]
    for n in listed:
        got = _lookup(cat, kind, n)[0]
        if got is not None and got["name"] == e["name"] and (kind != "support" or got["id"] == e["id"]):
            return True
    return False


def _check_claim(cl: Claim, path: str, cat: Catalogue, cfg: dict, add) -> None:
    hit = _has_number(cl.text, cfg["number_words"])
    if hit:
        add("error", "claim_number", f"{path}.text", f"claim states a number ({hit!r}); numbers come only from the engine, "
            "describe the mechanism in words without quantities")
    if not cl.cites:
        add("error", "claim_uncited", f"{path}.cites", "claim cites no catalogue entry; a claim without quotable PoE2 text is rejected")
    for j, ct in enumerate(cl.cites):
        cp = f"{path}.cites[{j}]"
        e = _resolve_ref(cat, ct["kind"], ct["id"], cp, add, cfg["cite_kinds"])
        if e is None:
            continue
        lines = texts(ct["kind"], e)
        if not lines:
            add("error", "claim_no_text", cp, f"{ct['kind']} {e['name']!r} has no PoE2 text in the catalogue to quote")
            continue
        q = _norm(ct["quote"])
        if len(q) < cfg["slate"]["quote_min_chars"]:
            add("error", "quote_short", f"{cp}.quote", f"quote shorter than {cfg['slate']['quote_min_chars']} characters")
        elif not (q in _norm(" ".join(lines)) or any(q in _norm(l) for l in lines)):
            add("error", "quote_mismatch", f"{cp}.quote", f"quote is not in the catalogue text of {e['name']!r} "
                "(shared name with different PoE1 behaviour?); quote it exactly", [l for l in lines][:3])


def _distance(a: dict, b: dict) -> list[str]:
    return [f for f in ARCH_FIELDS if a[f] != b[f]]


def _diversity(slate: Slate, rep: SlateReport, cfg: dict) -> None:
    dv, mx = cfg["diversity"], cfg["slate"]["max_kept"]
    kept: list[CandidateResult] = []
    for i, r in enumerate(rep.candidates):
        if r.errors:
            continue
        add = lambda code, msg: r.issues.append(Issue("error", code, f"candidates[{i}]", msg))  # noqa: E731
        near = next((k for k in kept if len(_distance(r.vector, k.vector)) < dv["min_differing_fields"]), None)
        if near is not None:
            same = [f for f in ARCH_FIELDS if r.vector[f] == near.vector[f]]
            add("near_duplicate", f"differs from kept candidate {near.name!r} on {len(_distance(r.vector, near.vector))} of "
                f"{len(ARCH_FIELDS)} archetype fields (need {dv['min_differing_fields']}); same: {', '.join(same)}")
        elif len(kept) >= mx:
            add("over_cap", f"slate already keeps {mx} candidates; later ones are dropped")
        else:
            r.kept = True
            kept.append(r)
    cons = slate.brief.get("constraints", {})
    for dim in ("delivery", "damage"):
        if dim in cons:
            continue
        vals = {k.vector[dim] for k in kept}
        if len(vals) >= dv["min_distinct"]:
            return
    open_dims = [d for d in ("delivery", "damage") if d not in cons]
    if open_dims and kept:
        rep.issues.append(Issue("error", "coverage", "candidates",
                                f"kept candidates cover too few distinct values of {' / '.join(open_dims)} (need {dv['min_distinct']} on at least one); "
                                "add candidates that differ on it, or fix it in brief.constraints",
                                [f"{d}: {sorted({k.vector[d] for k in kept})}" for d in open_dims]))
