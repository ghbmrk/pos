import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pos_catalogue import Catalogue  # noqa: E402
from pos_repin import check_tiers, diff_catalogues, revalidate_specs  # noqa: E402
from pos_repin import diff as diffmod  # noqa: E402
from pos_repin.__main__ import main  # noqa: E402
from pos_tiers.tiers import TierTable  # noqa: E402

E = lambda name, **kw: {"name": name, **kw}  # noqa: E731


def cat(sha, **over):
    d = {
        "schema": 1, "pob_sha": sha * 7 + "0" * 33, "tree_version": "0_5",
        "classes": [E("Witch", ascendancies=["Infernalist"])],
        "ascendancies": [E("Infernalist", **{"class": "Witch"})],
        "skills": [E("Fireball", id="FireballPlayer", skill_types=["Spell", "Fire"]),
                   E("Old Skill", id="OldPlayer", skill_types=["Spell"])],
        "supports": [E("Fire Mastery", id="SupFM", require_types=["Fire"])],
        "uniques": [E("Andvarius", base="Gold Ring"), E("Headhunter", base="Leather Belt")],
        "bases": [E("Gold Ring", type="Ring")],
        "keystones": [E("Chaos Inoculation", node=1, ascendancy=None, stats=[])],
        "notables": [E("Heart of Ice", node=2, ascendancy=None, stats=[])],
    }
    d.update(over)
    return d


def test_diff_categories():
    old = cat("a")
    new = cat(
        "b", tree_version="1_0",
        skills=[E("Fireball", id="FireballPlayer", skill_types=["Spell", "Fire", "Projectile"]),
                E("Newer Skill", id="NewPlayer", skill_types=["Spell"])],
        supports=[E("Fire Mastery I", id="SupFM", require_types=["Fire"])],
        uniques=[E("Andvarius", base="Gold Ring"), E("Headhunters", base="Leather Belt"), E("Brand New", base="Gold Ring")],
        notables=[E("Heart of Frost", node=2, ascendancy=None, stats=[])],
    )
    d = diff_catalogues(old, new)
    k = d.kinds
    assert k["skills"].removed == ["Old Skill"] and k["skills"].added == ["Newer Skill"]
    assert k["skills"].changed == [("Fireball", ["skill_types"])]
    assert k["supports"].renamed == [("Fire Mastery", "Fire Mastery I")]
    assert k["notables"].renamed == [("Heart of Ice", "Heart of Frost")]
    assert k["uniques"].possible_renamed == [("Headhunter (Leather Belt)", "Headhunters (Leather Belt)")]
    assert k["uniques"].added == ["Brand New (Gold Ring)"] and k["uniques"].removed == []
    assert k["bases"].empty and k["classes"].empty
    assert d.tree_version == ("0_5", "1_0") and d.breaking == 4
    text = diffmod.render(d)
    assert "(CHANGED)" in text and "Old Skill" in text


def test_identical_catalogues_have_no_diff():
    d = diff_catalogues(cat("a"), cat("a"))
    assert d.breaking == 0 and all(k.empty for k in d.kinds.values())


SPEC_OK = {"pob_sha": "aaaaaaa", "class": "Witch", "ascendancy": "Infernalist", "level": 90,
           "main_skill": {"gem": "Fireball"}, "tiers": ["starter"]}


def test_revalidate_reports_removed_and_ignores_old_pin(tmp_path):
    (tmp_path / "ok.yaml").write_text(yaml.safe_dump(SPEC_OK))
    (tmp_path / "gone.yaml").write_text(yaml.safe_dump({**SPEC_OK, "main_skill": {"gem": "Old Skill"}}))
    (tmp_path / "bad.yaml").write_text("not: a spec")
    new = Catalogue(cat("b", skills=[E("Fireball", id="FireballPlayer", skill_types=["Spell", "Fire"]),
                                       E("Old Skill Remastered", id="OldRe", skill_types=["Spell"])]))
    res = {Path(r.path).name: r for r in revalidate_specs(tmp_path, new)}
    assert res["ok.yaml"].ok and res["ok.yaml"].old_sha == "aaaaaaa"
    assert not res["gone.yaml"].ok
    assert any("Old Skill Remastered" in e for e in res["gone.yaml"].errors)  # suggestion surfaced
    assert not res["bad.yaml"].ok and res["bad.yaml"].old_sha is None
    assert revalidate_specs(tmp_path / "missing", new) == []


def test_tiercheck():
    table = TierTable.load()
    old = {"Foo", "FireResistance", "Removed"}
    new = {"Foo", "FireResistance", "BrandNewGroup", "AllResistances"}
    c = check_tiers(old, new, table)
    assert c.new_groups_unweighted == ["BrandNewGroup"]  # AllResistances is new but has a rule
    assert c.removed_groups == ["Removed"]
    assert "BaseSpirit" in c.dead_rules and "AllResistances" not in c.dead_rules
    assert c.stale_anchors == []
    table.raw["anchors"] = {"weapon": {"mid": {"div": 12.0, "date": "2026-12-20"}}}
    assert check_tiers(old, new, table).stale_anchors == ["weapon/mid: 12.0 div, dated 2026-12-20"]


def test_cli_report_exit_codes(tmp_path):
    old, new = cat("a"), cat("b", skills=[E("Fireball", id="FireballPlayer", skill_types=["Spell", "Fire"])])
    (tmp_path / "old.json").write_text(json.dumps(old))
    (tmp_path / "new.json").write_text(json.dumps(new))
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "s.yaml").write_text(yaml.safe_dump(SPEC_OK))
    args = ["report", "--old", str(tmp_path / "old.json"), "--new", str(tmp_path / "new.json"),
            "--specs", str(specs), "--out", str(tmp_path / "r.md"), "--skip-tiers"]
    assert main(args) == 0
    assert "Old Skill" in (tmp_path / "r.md").read_text()
    (specs / "s.yaml").write_text(yaml.safe_dump({**SPEC_OK, "main_skill": {"gem": "Old Skill"}}))
    assert main(args) == 1


def test_repin_script_usage():
    root = Path(__file__).resolve().parents[2]
    assert subprocess.run(["bash", str(root / "tools" / "repin.sh")], capture_output=True).returncode == 2
    assert subprocess.run(["bash", "-n", str(root / "tools" / "repin.sh")]).returncode == 0
