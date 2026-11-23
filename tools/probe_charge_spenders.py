"""L5b step 0: does PoB compute the per-charge bonus of charge spenders when charges are set?

For every non-hidden skill that consumes a charge on use (SkillConsumes<Type>ChargesOnUse), equip the first weapon base that
lets the skill evaluate, toggle `use<Type>Charges` (and the override count), and diff every output scalar.
Output: JSON (default evals/l5b/charge_spenders.json) + a table on stdout.
"""
import json, re, sys, glob, argparse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pos_engine.engine import PobEngine  # noqa: E402
from pos_catalogue.catalogue import Catalogue  # noqa: E402
from pos_pipeline.sweep import equip_probe_weapon  # noqa: E402

SK = ROOT / "third_party/PathOfBuilding-PoE2/src/Data/Skills"
WEAPONS = ["Barbarous Quarterstaff", "Crude Bow", "Wrapped Quarterstaff"]
TYPES = {"Power": "PowerCha", "Frenzy": "FrenzyCha", "Endurance": "EnduranceCha"}


def spenders():
    out = []
    for f in sorted(glob.glob(str(SK / "*.lua"))):
        txt = open(f, encoding="utf-8").read()
        for m in re.finditer(r'skills\["(\w+)"\] = \{(.*?)\n\}\n', txt, re.S):
            body = m.group(2)
            nm = re.search(r'\bname = "([^"]+)"', body)
            st = re.search(r"skillTypes = \{(.*?)\},\n", body)
            if not nm or not st or "support = true" in body or "hidden = true" in body:
                continue
            ch = [t for t in ("Power", "Frenzy", "Endurance") if f"SkillConsumes{t}ChargesOnUse" in st.group(1)]
            if ch:
                kind = "attack" if "SkillType.Attack]" in st.group(1) else "spell" if "SkillType.Spell]" in st.group(1) else "other"
                out.append({"skill": nm.group(1), "charges": ch, "kind": kind})
    return out


def weapon_bases(cat):
    want = ["Quarterstaff", "Bow", "Spear", "Crossbow", "Sword", "Mace", "Staff", "Wand", "Flail", "Dagger", "Axe", "Sceptre"]
    seen = {}
    for e in cat.entries("base"):
        t = e.get("type", "")
        for w in want:
            if w in t and w not in seen:
                seen[w] = e["name"]
    return list(seen.values())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(ROOT / "evals/l5b/charge_spenders.json")); a = ap.parse_args()
    cat = Catalogue.load(); bases = weapon_bases(cat); rows = []
    for sp in spenders():
        row = dict(sp, status="not_evaluable")
        for base in bases:
            with PobEngine() as e:
                e.new_build(); e.set_class("Monk"); e.set_level(90)
                try:
                    xml = equip_probe_weapon(cat, e, e.get_xml(), base); e.load_build_xml(xml)
                except Exception:
                    continue
                e.paste_skill(f"{sp['skill']} 20/0 1")
                for t in sp["charges"]:
                    off = e.set_config(options={f"use{t}Charges": False}, keys="all").get("stats", {})
                    on = e.set_config(options={f"use{t}Charges": True}, keys="all").get("stats", {})
                    if not off.get("TotalDPS") and not on.get("TotalDPS") and not off.get("FullDPS"):
                        continue
                    diff = {k: [off.get(k), on[k]] for k in on if isinstance(on[k], (int, float)) and off.get(k) != on[k]
                            and not k.startswith(("PowerCharge", "FrenzyCharge", "EnduranceCharge", "RemovableTotal", "TotalCharges"))
                            and "Removable" not in k}
                    row.setdefault("by_charge", {})[t] = {"base": base, "dps_off": off.get("TotalDPS"), "dps_on": on.get("TotalDPS"),
                                                           "dps_moves": off.get("TotalDPS") != on.get("TotalDPS"), "other_outputs_moved": sorted(diff)[:12]}
                if row.get("by_charge"):
                    row["status"] = "evaluated"; break
        rows.append(row); print(row["skill"], row["status"], json.dumps(row.get("by_charge", {}))[:300], flush=True)
    Path(a.out).write_text(json.dumps(rows, indent=1)); return rows


if __name__ == "__main__":
    main()
