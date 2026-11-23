"""Meta-lessons corpus (data/meta_lessons.yaml): anchors resolve on the pinned catalogue, levers exist, evidence is
sourced or labelled recall, and no past-meta example name reaches a client."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_pipeline import meta_lessons as ml  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def test_corpus_validates_on_pinned_catalogue():
    assert ml.validate() == []


def test_rendered_and_public_text_carry_no_past_meta_examples():
    rendered = ml.render()
    public = json.dumps(ml.public())
    anchors = {a["name"].casefold() for p in ml.patterns() for a in (p.get("poe2") or {}).get("anchors", [])}
    for p in ml.patterns():
        for e in p.get("eras", []):
            for x in e.get("examples", []):
                if x.casefold() in anchors:
                    continue          # also a verified PoE2 name (e.g. a keystone that kept its name)
                pat = rf"\b{re.escape(x)}\b"
                assert not re.search(pat, rendered, re.I), x
                assert not re.search(pat, public, re.I), x


def test_every_rendered_pattern_has_compounding_text_and_absent_ones_are_skipped():
    rendered = ml.render()
    for p in ml.patterns():
        shown = f"`{p['id']}`" in rendered
        assert shown == (not (p.get("poe2") or {}).get("absent")), p["id"]
        if shown:
            assert p["compounds"].strip() and p["limits"].strip()


def test_snapshot_evidence_holds_the_claimed_figures():
    snap = json.loads((ROOT / "data/meta/ninja-2026-11-23.json").read_text(encoding="utf-8"))
    fr = next(lg for lg in snap["games"]["poe2"] if lg["leagueName"] == "Forbidden Rites")
    assert fr["statistics"][0]["class"] == "Gemling Legionnaire" and round(fr["statistics"][0]["percentage"]) == 32
    cv = next(lg for lg in snap["games"]["poe1"] if lg["leagueName"] == "Covens")
    assert (cv["statistics"][0]["class"], cv["statistics"][0]["skill"]) == ("Chieftain", "Righteous Fire")


def test_validate_catches_a_poe1_anchor_and_unknown_lever(monkeypatch):
    bad = [dict(ml.patterns()[0], poe2={"anchors": [{"kind": "support", "name": "Elemental Overload"}]}, levers=["nope"])]
    monkeypatch.setattr(ml, "patterns", lambda: bad)
    probs = ml.validate()
    assert any("Elemental Overload" in p for p in probs) and any("'nope'" in p for p in probs)
