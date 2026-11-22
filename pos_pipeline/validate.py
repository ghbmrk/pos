"""Validate a BuildSpec against the pinned catalogue, tier table and rules. Reports; never repairs silently."""
from __future__ import annotations

from dataclasses import dataclass, field

from pos_catalogue import Catalogue, can_support
from pos_tiers.tiers import TierTable

from . import data
from .spec import BuildSpec

FLOOR_FLAGS = {"resist_capped", "attributes_met"}


@dataclass
class Issue:
    severity: str  # error | warning
    code: str
    path: str
    message: str
    suggestions: list[str] = field(default_factory=list)
    confidence: str | None = None  # limitations only: verified | suspected


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)
    metric: str | None = None          # objective metric the run will rank by (None = unresolved)
    metric_note: str | None = None
    profile_hash: str | None = None    # cache-key component for the config profile

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


def _lookup(cat: Catalogue, kind: str, text: str):
    """Skill/support by catalogue id or gem_id first, else resolve() by name. Returns (entry|None, Resolution|None)."""
    if kind in ("skill", "support"):
        for e in cat.entries(kind):
            if text in (e["id"], e.get("gem_id")):
                return e, None
    r = cat.resolve(kind, text)
    return r.entry, r


def validate(spec: BuildSpec, cat: Catalogue, tiers: TierTable | None = None) -> Report:
    rep = Report()
    add = lambda sev, code, path, msg, sug=(), conf=None: rep.issues.append(Issue(sev, code, path, msg, list(sug), conf))  # noqa: E731

    def resolve(kind: str, text: str, path: str):
        entry, r = _lookup(cat, kind, text)
        if entry is None:
            if r.status == "ambiguous":
                add("error", "ambiguous", path, f"{kind} {text!r} matches several entries; pick one",
                    [f"{m['name']} ({m.get('base', m.get('id', ''))})" for m in r.matches])
            else:
                add("error", "unresolved", path, f"{kind} {text!r} not in catalogue {cat.pob_sha[:7]}",
                    [s["name"] for s in r.suggestions])
        return entry

    # pob pin
    if not cat.pob_sha.startswith(spec.pob_sha) or len(spec.pob_sha) < 7:
        add("error", "pob_sha", "pob_sha", f"spec pinned to {spec.pob_sha!r} but catalogue is {cat.pob_sha[:7]}; "
            "re-validate against the matching catalogue (>= 7 hex chars)")

    # class / ascendancy
    cls = resolve("class", spec.class_, "class")
    asc_names = set(cls["ascendancies"]) if cls else set()
    if spec.ascendancy:
        asc = resolve("ascendancy", spec.ascendancy, "ascendancy")
        if asc and cls and asc["name"] not in asc_names:
            add("error", "ascendancy_class", "ascendancy", f"{asc['name']} belongs to {asc['class']}, not {cls['name']}",
                sorted(asc_names))

    # level
    lv = data.rules()["level"]
    if not lv["min"] <= spec.level <= lv["max"]:
        add("error", "level", "level", f"level {spec.level} outside {lv['min']}-{lv['max']}")

    # main skill
    skill = resolve("skill", spec.main_skill, "main_skill.gem")
    if skill is None and spec.main_skill:
        sup, _ = _lookup(cat, "support", spec.main_skill)
        if sup:
            add("error", "support_as_skill", "main_skill.gem", f"{sup['name']} is a support gem, not a skill")

    # fixed supports
    _check_supports(spec, cat, skill, resolve, add)

    # fixed passives / uniques
    stats: list[str] = []
    for i, n in enumerate(spec.keystones):
        e = resolve("keystone", n, f"fixed.keystones[{i}]")
        stats += (e or {}).get("stats", [])
    for i, n in enumerate(spec.notables):
        e = resolve("notable", n, f"fixed.notables[{i}]")
        if e and e.get("ascendancy") and spec.ascendancy and not _asc_ok(cat, spec, e):
            add("error", "notable_ascendancy", f"fixed.notables[{i}]",
                f"{e['name']} is a {e['ascendancy']} node; spec ascendancy is {spec.ascendancy}")
        stats += (e or {}).get("stats", [])
    seen_u: set[str] = set()
    for i, n in enumerate(spec.uniques):
        e = resolve("unique", n, f"fixed.uniques[{i}]")
        if e:
            if e["name"] in seen_u:
                add("error", "duplicate", f"fixed.uniques[{i}]", f"unique {e['name']} listed twice (one per name)")
            seen_u.add(e["name"])

    # axes
    _check_axes(spec, cat, cls, resolve, add)

    # tiers
    tiers = tiers or TierTable.load()
    known = tiers.tier_names
    if not spec.tiers:
        add("error", "tiers", "tiers", "at least one tier required", known)
    for i, t in enumerate(spec.tiers):
        if t not in known:
            add("error", "tier", f"tiers[{i}]", f"unknown tier {t!r}", known)
    if len(set(spec.tiers)) != len(spec.tiers):
        add("error", "duplicate", "tiers", "tiers listed more than once")

    # config profile
    profs = data.profiles()
    if spec.config_profile in profs:
        rep.profile_hash = data.profile_hash(spec.config_profile)
    else:
        add("error", "config_profile", "config_profile", f"unknown config profile {spec.config_profile!r}", sorted(profs))

    # objective metric + floors
    _check_objective(spec, skill, rep, add)

    # limitations (verified ones and catalogue-derived suspicions): warnings, never silent
    _limitations(spec, skill, stats, add)
    return rep


def _asc_ok(cat, spec, node) -> bool:
    asc = cat.resolve("ascendancy", spec.ascendancy).entry
    axis = set(spec.axes.get("ascendancy", []))
    return node["ascendancy"] == (asc or {}).get("name") or node["ascendancy"] in axis


def _check_supports(spec, cat, skill, resolve, add) -> None:
    sup_entries = []
    for i, n in enumerate(spec.supports):
        e = resolve("support", n, f"fixed.supports[{i}]")
        if e:
            sup_entries.append((i, e))
    fams: dict[str, str] = {}
    ids: set[str] = set()
    for i, e in sup_entries:
        if e["id"] in ids:
            add("error", "duplicate", f"fixed.supports[{i}]", f"{e['name']} listed twice")
        ids.add(e["id"])
        for f in e.get("family") or []:
            if f in fams and fams[f] != e["id"]:
                add("error", "support_family", f"fixed.supports[{i}]",
                    f"{e['name']} shares support family {f!r} with an earlier support; only one per family")
            fams.setdefault(f, e["id"])
    ms = data.rules()["max_supports"]
    if len(spec.supports) > ms["value"]:
        add("warning" if not ms["verified"] else "error", "socket_limit", "fixed.supports",
            f"{len(spec.supports)} fixed supports exceed the {ms['value']}-support limit"
            + ("" if ms["verified"] else " (limit unverified against PoB, see data/rules.yaml)"))
    if not skill:
        return
    # Supports can add skill types that later supports need (add_types). Order-insensitive fixed point:
    # permissive on purpose; PoB's own ordering rule is unchecked (G5).
    types = set(skill.get("skill_types") or [])
    pending = list(sup_entries)
    progress = True
    while pending and progress:
        progress = False
        for item in list(pending):
            _, e = item
            if can_support(e, {"skill_types": sorted(types)}):
                types |= set(e.get("add_types") or [])
                pending.remove(item)
                progress = True
    for i, e in pending:
        add("error", "support_incompatible", f"fixed.supports[{i}]",
            f"{e['name']} cannot support {skill['name']} (type requirement "
            f"{e.get('require_types')} / exclusion {e.get('exclude_types')} vs skill types)")
    is_minion = bool({"Minion", "CreatesMinion"} & set(skill.get("skill_types") or []))
    for i, e in sup_entries:
        if "Minion" in (e.get("tags") or "") and not is_minion and (i, e) not in pending:
            add("warning", "minion_support", f"fixed.supports[{i}]",
                f"{e['name']} is tagged Minion but {skill['name']} is not a minion skill; "
                "it may only affect minions, so check it does something")


def _check_axes(spec, cat, cls, resolve, add) -> None:
    allowed = data.rules()["axes"]
    base_types = {b["type"].casefold(): b["type"] for b in cat.entries("base")}
    for axis, vals in spec.axes.items():
        p = f"axes.{axis}"
        if axis not in allowed:
            add("error", "axis", p, f"unknown axis {axis!r}", allowed)
            continue
        if not vals:
            add("error", "axis", p, "axis has no values")
        if len(set(vals)) != len(vals):
            add("error", "duplicate", p, "axis lists a value twice")
        for i, v in enumerate(vals):
            vp = f"{p}[{i}]"
            if axis == "ascendancy":
                a = resolve("ascendancy", v, vp)
                if a and cls and a["name"] not in cls["ascendancies"]:
                    add("error", "ascendancy_class", vp, f"{a['name']} belongs to {a['class']}, not {cls['name']}")
            elif axis == "main_skill":
                resolve("skill", v, vp)
            elif axis == "weapon_base":
                for tok in v.split("+"):
                    if tok.strip().casefold() not in base_types:
                        near = [t for k, t in base_types.items() if tok.strip().casefold() in k]
                        add("error", "unresolved", vp, f"base type {tok!r} not in catalogue", near or sorted(base_types.values()))


def _check_objective(spec, skill, rep, add) -> None:
    m = data.metrics()
    keys = set(m["stat_keys"])
    if spec.maximise == "auto":
        if skill:
            r = data.metric_for(skill.get("skill_types") or [])
            rep.metric, rep.metric_note = r["metric"], r["note"]
            if r["metric"] is None:
                add("error", "no_metric", "objective.maximise",
                    f"no engine metric for {skill['name']}: {r['note']} Name one of {sorted(keys)} explicitly.")
    elif spec.maximise in keys:
        rep.metric, rep.metric_note = spec.maximise, "named in spec"
    else:
        add("error", "metric", "objective.maximise", f"unknown metric {spec.maximise!r}", sorted(keys))
    for k, v in spec.floors.items():
        p = f"objective.floors.{k}"
        if k not in FLOOR_FLAGS and k not in keys:
            add("error", "floor", p, f"unknown floor {k!r}", sorted(FLOOR_FLAGS | keys))
        elif k in FLOOR_FLAGS and not isinstance(v, bool):
            add("error", "floor", p, f"{k} must be true/false")
        elif k in keys and not (v == "tier_default" or (isinstance(v, (int, float)) and not isinstance(v, bool))):
            add("error", "floor", p, f"{k} must be a number or 'tier_default'")


def _limitations(spec, skill, stats, add) -> None:
    names = {skill["name"]} if skill else set()
    types = set(skill.get("skill_types") or []) if skill else set()
    for lim in data.limitations():
        mt = lim["match"]
        hit = ("skill" in mt and mt["skill"] in names) or ("skill_type" in mt and mt["skill_type"] in types) \
            or ("stat_prefix" in mt and any(s.startswith(mt["stat_prefix"]) for s in stats))
        if hit:
            add("warning", "limitation", "main_skill" if "stat_prefix" not in mt else "fixed", lim["note"], conf=lim["confidence"])
