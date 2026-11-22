import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_catalogue import Catalogue, can_support, export_catalogue  # noqa: E402
from pos_catalogue.export import CATALOGUE_DIR, pob_sha  # noqa: E402
from pos_engine.paths import bundled_luajit, pob_src_dir  # noqa: E402

needs_pob = pytest.mark.skipif(
    bundled_luajit() is None or not (pob_src_dir() / "Data" / "Gems.lua").exists(),
    reason="needs tools/build_luajit.sh and the PoB submodule",
)


def _entry(name, **kw):
    return {"name": name, **kw}


@pytest.fixture
def small():
    return Catalogue({
        "pob_sha": "abc1234" + "0" * 33,
        "classes": [_entry("Witch", ascendancies=["Infernalist"])],
        "ascendancies": [_entry("Infernalist", **{"class": "Witch"})],
        "skills": [
            _entry("Fireball", id="FireballPlayer", skill_types=["Spell", "Fire", "Projectile"]),
            _entry("Raise Zombie", id="ZombiePlayer", skill_types=["Minion", "Spell", "Fire"]),
        ],
        "supports": [
            _entry("Fire Mastery", id="SupFM", require_types=["Fire"], exclude_types=["Minion"]),
            _entry("Abiding Hex", id="SupAH", require_types=["AppliesCurse"]),
            _entry("Any Support", id="SupAny"),
            _entry("Either", id="SupEither", require_types=["Fire", "Cold", "OR"]),
            _entry("Both", id="SupBoth", require_types=["Fire", "Projectile", "AND"]),
        ],
        "uniques": [_entry("Grand Spectrum", base="Ruby"), _entry("Grand Spectrum", base="Emerald"), _entry("Andvarius", base="Gold Ring")],
        "bases": [_entry("Gold Ring")],
        "keystones": [_entry("Chaos Inoculation")],
        "notables": [_entry("Heart of Ice")],
    })


def test_exact_ignores_case_and_punctuation(small):
    r = small.resolve("skill", "  FIREBALL ")
    assert r.status == "exact" and r.entry["id"] == "FireballPlayer"
    assert small.resolve("notable", "heart of ice").status == "exact"


def test_ambiguous_returns_all_candidates(small):
    r = small.resolve("unique", "grand spectrum")
    assert r.status == "ambiguous" and {m["base"] for m in r.matches} == {"Ruby", "Emerald"} and r.entry is None


def test_unresolved_gives_suggestions_not_a_guess(small):
    r = small.resolve("skill", "fire ball")
    assert r.status == "unresolved" and r.entry is None
    assert [s["name"] for s in r.suggestions][0] == "Fireball"
    assert small.resolve("skill", "zzzzzz").suggestions == []


def test_kind_is_respected(small):
    assert small.resolve("support", "Fireball").status == "unresolved"
    with pytest.raises(ValueError):
        small.resolve("gem", "Fireball")


def test_type_expressions(small):
    fb, zombie = small.get("skill", "FireballPlayer"), small.get("skill", "ZombiePlayer")
    sup = {s["id"]: s for s in small.data["supports"]}
    assert can_support(sup["SupFM"], fb) and not can_support(sup["SupFM"], zombie)
    assert not can_support(sup["SupAH"], fb)
    assert can_support(sup["SupAny"], fb)
    assert can_support(sup["SupEither"], fb) and can_support(sup["SupEither"], zombie)
    assert can_support(sup["SupBoth"], fb) and not can_support(sup["SupBoth"], zombie)
    assert {s["id"] for s in small.supporting("FireballPlayer")} == {"SupFM", "SupAny", "SupEither", "SupBoth"}


def test_get_missing_raises(small):
    with pytest.raises(KeyError):
        small.get("skill", "Nope")


# --- against the real pinned PoB ---------------------------------------------------------------

@pytest.fixture(scope="module")
def real():
    return Catalogue.load(CATALOGUE_DIR / "601768b.json")


def test_committed_catalogue_shape(real):
    d = real.data
    assert d["pob_sha"].startswith("601768b") and d["schema"] == 2
    assert len(d["skills"]) > 300 and len(d["supports"]) > 500 and len(d["bases"]) > 1000
    assert len(d["classes"]) == 8 and len(d["keystones"]) > 20 and len(d["notables"]) > 1000
    assert all(s["skill_types"] for s in d["skills"] if not s.get("no_skill_data"))
    ids = [s["id"] for s in d["skills"] + d["supports"]]
    assert len(ids) == len(set(ids))


def test_real_resolve_and_compatibility(real):
    fb = real.resolve("skill", "fireball").entry
    assert fb["id"] == "FireballPlayer" and "Fire" in fb["skill_types"] or "Spell" in fb["skill_types"]
    supported = {s["name"] for s in real.supporting(fb["id"])}
    assert "Fire Penetration I" in supported and "Abiding Hex" not in supported
    assert real.resolve("support", "fire penetration").status == "unresolved"
    assert any(s["name"] == "Fire Penetration I" for s in real.resolve("support", "fire penetration").suggestions)
    assert real.resolve("ascendancy", "Deadeye").entry["class"] == "Ranger"
    assert real.resolve("keystone", "zealots oath").status == "exact"
    assert real.resolve("base", "Aberrant Sledge").status == "exact"


@needs_pob
def test_committed_catalogue_matches_pinned_pob(tmp_path, real):
    """Fails after a re-pin until the catalogue is re-exported (python -m pos_catalogue export)."""
    committed = CATALOGUE_DIR / f"{pob_sha()[:7]}.json"
    assert committed.exists(), "PoB pin moved: re-export the catalogue (tools/repin.sh does this)"
    path = export_catalogue(out_dir=tmp_path)
    assert path.read_text(encoding="utf-8") == committed.read_text(encoding="utf-8")


# --- ideation queries (I2) ---------------------------------------------------------------------

def test_committed_catalogue_has_text(real):
    d = real.data
    assert sum(1 for g in d["skills"] + d["supports"] if g.get("description")) > 900
    assert all("lines" in u for u in d["uniques"])
    assert sum(1 for u in d["uniques"] if u["lines"]) >= len(d["uniques"]) - 5
    for u in d["uniques"]:  # header lines never leak into mod text
        assert not any(l["text"].startswith(("Variant:", "Implicits:", "Requires Level", "League:", "Source:", "{")) for l in u["lines"])


def test_unique_variant_lines_use_newest_variant(real):
    ch = real.explain("unique", "Carnage Heart")
    assert "(100-200)% increased amount of Life Leeched" in ch["text"]
    assert "100% increased amount of Life Leeched" not in ch["text"]
    assert ch["variants"][-1] == "Current" and ch["implicit_count"] == 1
    assert any(l.get("variants") == [1] for l in ch["all_lines"])  # old variants stay available


def test_explain_kinds(real):
    s = real.explain("support", "SupportAbidingHexPlayer")
    assert "Curse" in s["text"][0] and s["require_types"] == ["AppliesCurse"]
    k = real.explain("keystone", "Ancestral Bond")
    assert "Your Totem Limit is doubled" in k["text"]
    with pytest.raises(KeyError):
        real.explain("keystone", "Nope")


def test_search_filters(real):
    hits = real.search("support", skill_types=["AppliesCurse"], limit=5)
    assert hits and all("AppliesCurse" in h["require_types"] for h in hits)
    assert all(n["ascendancy"] == "Invoker" for n in real.search("notable", ascendancy="Invoker"))
    assert real.search("unique", text="freeze buildup lightning damage converted")
    assert real.search("keystone", text="totem")
    assert real.search("support", text="zzzzqq") == []
    assert real.search("skill", tags=["spell"], limit=3)


def test_word_start_matching():
    c = Catalogue({"pob_sha": "0" * 40, "classes": [], "ascendancies": [], "skills": [], "supports": [], "uniques": [],
                   "bases": [], "keystones": [{"name": "A", "node": 1, "stats": ["Fireball is hot", "Misfire is not"]}], "notables": []})
    assert c.search("keystone", text="fire")
    assert c.search("keystone", text="hot fire")
    assert not c.search("keystone", text="ire")


def test_enablers_and_bridges(real):
    e = real.enablers("Totem")
    assert e["keystones"] and e["notables"] and set(e) == {"supports_adding", "keystones", "notables", "uniques"}
    assert any("Freeze" in " ".join(real_text) for real_text in
               [[l["text"] for l in u["lines"]] for u in real.bridges("Freeze", "Lightning")["uniques"]])
    b = real.bridges("Armour", "Energy Shield", limit=3)
    assert all(len(v) <= 3 for v in b.values())
