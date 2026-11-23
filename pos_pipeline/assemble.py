"""Assembler (G3b, docs/assemble.md): BuildSpec + variant -> PoB build, with round-trip checks.

Uses only PobEngine calls, so the PoB XML it returns is PoB's own serialisation. Problems found by the
round trip are `Issue`s (same type as the validator's), never silent repairs.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any

from pos_catalogue import Catalogue
from pos_engine.engine import PobEngine

from . import data
from .spec import BuildSpec
from .validate import Issue, _lookup

DEFAULT_GEM_LEVEL = 20
# Axes the assembler applies. weapon_base is gear placement, which belongs to the gear search (G7).
APPLIED_AXES = ("ascendancy", "main_skill")
DEFERRED_AXES = ("weapon_base",)


@dataclass
class Assembled:
    variant: dict[str, str]
    xml: str = ""
    main_skill: str | None = None
    stats: dict[str, Any] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    deferred_axes: dict[str, str] = field(default_factory=dict)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def ok(self) -> bool:
        return not self.errors and bool(self.xml)


def variants(spec: BuildSpec) -> list[dict[str, str]]:
    """Cartesian product of the spec's axes (one seed build per combination); [{}] when there are none."""
    if not spec.axes:
        return [{}]
    names = sorted(spec.axes)
    return [dict(zip(names, combo)) for combo in itertools.product(*(spec.axes[n] for n in names))]


def unparsed_lines(engine: PobEngine, raw: str) -> list[dict]:
    """Mod lines PoB keeps but cannot parse (they contribute nothing). Raises ValueError if the item itself
    does not parse (unknown base). Gear search must reject candidates with any entry here."""
    r = engine.call("check_item", raw=raw)
    if not r.get("ok"):
        raise ValueError(r.get("error", "item not parsed"))
    return r["unparsed"]


def _gem_line(name: str) -> str:
    return f"{name} {DEFAULT_GEM_LEVEL}/0  1"


def assemble(spec: BuildSpec, cat: Catalogue, engine: PobEngine, variant: dict[str, str] | None = None) -> Assembled:
    """Build `spec` (with `variant` overriding ascendancy / main_skill) in `engine`, check it, return its XML.

    The spec should already pass `validate`; this re-resolves names and reports anything the engine contradicts.
    """
    variant = dict(variant or {})
    out = Assembled(variant=variant)
    add = lambda sev, code, path, msg, sug=(): out.issues.append(Issue(sev, code, path, msg, list(sug), None))  # noqa: E731
    out.deferred_axes = {k: v for k, v in variant.items() if k in DEFERRED_AXES}
    for k in variant:
        if k not in APPLIED_AXES + DEFERRED_AXES:
            add("error", "axis", f"axes.{k}", f"assembler does not know axis {k!r}")

    def entry(kind: str, text: str, path: str):
        e, r = _lookup(cat, kind, text)
        if e is None:
            add("error", "unresolved", path, f"{kind} {text!r} not resolvable ({r.status if r else 'unknown'})",
                [s["name"] for s in (r.suggestions if r else [])])
        return e

    asc = variant.get("ascendancy", spec.ascendancy)
    skill = entry("skill", variant.get("main_skill", spec.main_skill), "main_skill")
    sups = [entry("support", s, f"fixed.supports[{i}]") for i, s in enumerate(spec.supports)]
    keystones = [entry("keystone", k, f"fixed.keystones[{i}]") for i, k in enumerate(spec.keystones)]
    notables = [entry("notable", n, f"fixed.notables[{i}]") for i, n in enumerate(spec.notables)]
    if out.errors or skill is None:
        return out

    r = engine.new_build()  # noqa: F841
    sc = engine.set_class(spec.class_, asc)
    if not sc.get("ok", True):
        add("error", "class", "class", f"engine rejected class/ascendancy {spec.class_}/{asc}: {sc}")
        return out
    engine.set_level(spec.level)

    text = "\n".join(_gem_line(e["name"]) for e in [skill] + [s for s in sups if s])
    ps = engine.paste_skill(text)
    if ps.get("ok") is False:
        add("error", "skill", "main_skill", ps.get("error", "paste_skill failed"))
        return out

    for kind, entries in (("keystone", keystones), ("notable", notables)):
        for e in entries:
            res = engine.alloc_passive(e["node"])
            if not res.get("ok", False):
                add("error", "passive", kind, f"could not allocate {e['name']}: {res.get('error', res)}")

    slots_used: set[str] = set()
    for i, u in enumerate(spec.uniques):
        e = entry("unique", u, f"fixed.uniques[{i}]")
        if e is None:
            continue
        _equip_unique(engine, e, slots_used, add, f"fixed.uniques[{i}]")

    prof = data.profiles()[spec.config_profile]
    engine.set_config(options={**(prof.get("options") or {}), **data.condition_options(spec.conditions)} or None, custom_mods=prof.get("custom_mods") or None)

    _round_trip(engine, spec, skill, sups, keystones, notables, asc, out, add)
    out.xml = engine.get_xml()
    return out


def assemble_companion(spec: BuildSpec, cat: Catalogue, engine: PobEngine) -> Assembled:
    """Companion as its own PoB build (`separate_build`, docs/second-actor.md section 3): the player's class and level, the
    companion's skill group, no passives or uniques. One skill group: the Squire takes one skill plus its supports
    (owner 2026-11-23, data/actors.yaml `skills_source`); the validator enforces the count."""
    from dataclasses import replace
    out = Assembled(variant={})
    comp = spec.companion
    if comp is None or not comp.skills:
        out.issues.append(Issue("error", "companion_skills", "companion.skills", "no companion skill to assemble", [], None))
        return out
    if len(comp.skills) > 1:
        out.issues.append(Issue("error", "companion_skills", "companion.skills",
                                "separate_build assembles one companion skill group (the Squire takes one skill plus its supports)",
                                [], None))
        return out
    sk = comp.skills[0]
    sub = replace(spec, main_skill=sk.gem, supports=list(sk.supports), keystones=[], notables=[], uniques=[], axes={}, companion=None)
    return assemble(sub, cat, engine, None)


def _equip_unique(engine: PobEngine, e: dict, slots_used: set[str], add, path: str) -> None:
    t = engine.call("unique_text", name=e["name"], base=e.get("base"))
    if not t.get("ok"):
        add("error", "unique", path, t.get("error", "unique text unavailable"))
        return
    raw = t["raw"]
    if not raw.lstrip().lower().startswith("rarity:"):
        raw = "Rarity: UNIQUE\n" + raw
    bad = engine.call("check_item", raw=raw)
    if not bad.get("ok"):
        add("error", "unique", path, bad.get("error", "unique did not parse"))
        return
    # A second ring/weapon-hand goes to the second slot instead of replacing the first.
    base_type = bad.get("base") or ""
    slot = None
    if base_type == "Ring":
        slot = "Ring 2" if "Ring 1" in slots_used else "Ring 1"
    res = engine.add_item(raw, slot=slot)
    if not res.get("ok"):
        add("error", "unique", path, f"could not equip {e['name']}: {res.get('error')}")
        return
    slots_used.add(res["slot"])


def _round_trip(engine, spec, skill, sups, keystones, notables, asc, out: Assembled, add) -> None:
    chk = engine.call("check_build")
    out.main_skill = chk.get("mainSkill")
    if not out.main_skill:
        add("error", "no_main_skill", "main_skill", "PoB resolved no main skill")
    elif out.main_skill != skill["name"]:
        add("error", "main_skill_mismatch", "main_skill", f"PoB main skill is {out.main_skill!r}, spec says {skill['name']!r}")
    for g in chk.get("unrecognisedGems", []):
        add("error", "unrecognised_gem", "main_skill", f"PoB did not recognise gem {g!r}")
    main = next((g for g in chk.get("gems", []) if g["group"] >= 1 and g.get("label") == skill["name"]), None)
    if main is not None and main["supports"] != len(sups):
        add("error", "supports_missing", "fixed.supports",
            f"{len(sups)} supports in spec but PoB socketed {main['supports']} (unrecognised or rejected)")
    for u in chk.get("unparsed", []):
        add("warning", "unparsed_mod", f"item[{u['slot']}]",
            f"PoB cannot parse mod line {u['line']!r}; it contributes nothing to the calc")
    for k, v in (chk.get("warnings") or {}).items():
        add("error" if k == "socketLimitWarning" else "warning", "pob_warning", k, f"PoB warning {k}: {v}")
    b = engine.get_build()
    have = set(b.get("keystones", [])) | set(b.get("notables", [])) | set(b.get("ascendancyNotables", []))
    for e in keystones + notables:
        if e["name"] not in have:
            add("error", "passive_missing", e["name"], f"{e['name']} not allocated after build")
    if b.get("level") != spec.level:
        add("error", "level", "level", f"PoB level {b.get('level')} != spec {spec.level}")
    if (asc or "None") != b.get("ascendancy"):
        add("error", "ascendancy", "ascendancy", f"PoB ascendancy {b.get('ascendancy')!r} != {asc!r}")
    out.stats = engine.get_stats()["stats"]
    if out.main_skill and not any(out.stats.get(k) for k in ("TotalDPS", "FullDPS", "CombinedDPS")):
        add("warning", "zero_dps", "main_skill",
            "main skill computes 0 DPS in the seed (expected until gear is placed for attack skills)")


def import_pob(code_or_xml: str, cat: Catalogue, engine: PobEngine, tiers: list[str] | None = None) -> tuple[BuildSpec, list[Issue]]:
    """PoB share code (or XML) -> BuildSpec: class, ascendancy, level, main skill + supports, allocated
    keystones/notables, equipped uniques. Anything not representable in a spec is dropped and listed as an
    `import_dropped` warning, so a round trip never silently loses content."""
    issues: list[Issue] = []
    warn = lambda code, path, msg: issues.append(Issue("warning", code, path, msg, [], None))  # noqa: E731
    if code_or_xml.lstrip().startswith("<"):
        engine.load_build_xml(code_or_xml)
    else:
        engine.load_build_code(code_or_xml)
    b = engine.get_build()
    group = b.get("mainSkillGroup") or []
    if not group:
        raise ValueError("imported build has no main skill group")

    def pick(kind: str, name: str, path: str):
        e, r = _lookup(cat, kind, name)
        if e is None:
            warn("import_dropped", path, f"{kind} {name!r} not in catalogue {cat.pob_sha[:7]} ({r.status}); dropped")
        return e

    skill = pick("skill", group[0]["name"], "main_skill")
    if skill is None:
        raise ValueError(f"main skill {group[0]['name']!r} not in catalogue")
    supports = [e["id"] for g in group[1:] if (e := pick("support", g["name"], "fixed.supports"))]
    keystones = [e["name"] for n in b.get("keystones", []) if (e := pick("keystone", n, "fixed.keystones"))]
    notables = [e["name"] for n in b.get("notables", []) if (e := pick("notable", n, "fixed.notables"))]
    uniques = []
    for slot, it in (b.get("gear") or {}).items():
        if it.get("name") and engine.call("unique_text", name=it["name"], base=it.get("base")).get("ok"):
            u = pick("unique", it["name"], f"gear[{slot}]")
            if u:
                uniques.append(u["name"])
        else:
            warn("import_dropped", f"gear[{slot}]", f"{it.get('name')!r} is not a unique; gear is searched per tier, not imported")
    if b.get("ascendancyNotables"):
        notables += [n for n in b["ascendancyNotables"] if pick("notable", n, "fixed.notables")]
    asc = b.get("ascendancy")
    spec = BuildSpec(
        pob_sha=cat.pob_sha[:7], class_=b["class"], ascendancy=None if asc in (None, "None") else asc,
        level=b["level"], main_skill=skill["id"], supports=supports, keystones=keystones, notables=notables,
        uniques=uniques, tiers=list(tiers or []),
    )
    return spec, issues
