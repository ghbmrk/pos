"""Exploit-primitive scan over the pinned catalogue plus the 1.0 text corpus.

Each line of rule text (unique mods, notables, keystones, support and skill
descriptions, 1.0 entries) is tagged with exploit primitives (P1-P7) and with
families. Output: JSON of hits, and a per-family x per-primitive count table so
coverage can be checked before triage. No ranking is done here.
"""
import json, re, sys, collections

CAT = "data/catalogue/601768b.json"
NEW = "tools/census/new_1_0.json"

PRIMS = {
 # P1 uncapped per-X scaling: "per N X" / "for each" without a cap word on the same line
 "P1_uncapped_per_x": (re.compile(r"\b(per|for each|for every)\b", re.I),
                       re.compile(r"\b(up to|maximum of|max(imum)? \d|limit|cannot exceed|counting up to)\b", re.I)),
 # P2 count-as / treated-as without paying the cost
 "P2_count_as": (re.compile(r"(count(s)? as|considered|treated as|as though|as if|also (count|apply|grant)|do(es)? not (consume|count|break|remove)|without (consuming|spending|removing)|no charge requirement|instead of)", re.I), None),
 # P3 cost and payoff in different units (life for damage, spirit, charges, minion life...)
 "P3_cost_unit_mismatch": (re.compile(r"(paid by|cost(s)? .*life|sacrifice|lose life|take .*damage equal|reserve|consume|expend|spend)", re.I), None),
 # P4 non-damage stat converted to damage or to a scaler
 "P4_stat_to_damage": (re.compile(r"((damage|added|extra).*(equal to|per|based on).*(armour|evasion|life|mana|energy shield|spirit|strength|dexterity|intelligence|block|resist|movement speed|attribute|ward|guard|power|rage|valour|glory|darkness))|((armour|evasion|life|mana|energy shield|spirit|strength|block|resistance|movement speed).*(also applies to|as extra|converted to).*damage)", re.I), None),
 # P5 recursion/copies: triggers, repeats, copies, echoes, mirages, shades, totems copying
 "P5_recursion_copy": (re.compile(r"(trigger|repeat|copy|copies|echo|afterimage|mirage|shade|additional time|twice|again|another|duplicate|clone|mimic|reflect)", re.I), None),
 # P6 snapshot / per-use on long use / timing
 "P6_snapshot_timing": (re.compile(r"(on use|when you use|next (\d+ |few )?(attack|skill|strike|spell|melee)|empower|stored|accumulat|build ?up|stages?|while channell|after channell|lingers|paused|infinite duration|cannot expire|recently)", re.I), None),
 # P7 guard phrases (used to find siblings that lack them)
 "P7_guard": (re.compile(r"(you use yourself|cannot (support|be|trigger)|once (every|per)|cooldown|non-triggered|not triggered|triggered skills cannot|only one|limit \d|maximum of \d|up to \d|counting up to)", re.I), None),
}

FAM = {
 "class:Warrior": r"warrior|titan|warbringer|smith of kitava|mace|slam|warcry|endurance",
 "class:Ranger": r"ranger|deadeye|pathfinder|bow|arrow|frenzy",
 "class:Huntress": r"huntress|amazon|ritualist|spirit walker|spear|parr",
 "class:Mercenary": r"mercenary|tactician|witchhunter|gemling|crossbow|grenade|bolt",
 "class:Monk": r"monk|invoker|acolyte|martial artist|chayula|quarterstaff|unarmed",
 "class:Sorceress": r"sorceress|stormweaver|chronomancer|disciple of varashta|djinn|staff",
 "class:Witch": r"witch|infernalist|blood mage|lich|abyssal",
 "class:Druid": r"druid|oracle|shaman|talisman|shapeshift|bear|wolf|wyvern|plant",
 "class:Duelist(1.0)": r"duelist|sword|ready stance|blood stance|sand stance|wind blade|buried blade",
 "class:Shadow(1.0)": r"shadow|dagger|trap|darkness|stealth|ambush|shade|remnant|prospero",
 "class:Knight(1.0)": r"knight|squire|valour|banner|glory|honourbound|guard\b",
 "weapon:mace": r"\bmaces?\b", "weapon:sword": r"\bswords?\b", "weapon:axe": r"\baxes?\b",
 "weapon:dagger": r"\bdaggers?\b", "weapon:spear": r"\bspears?\b", "weapon:bow": r"\bbows?\b",
 "weapon:crossbow": r"crossbow", "weapon:quarterstaff": r"quarterstaff", "weapon:flail": r"flail",
 "weapon:wand/staff/sceptre": r"\bwands?\b|\bstaff\b|sceptre", "weapon:unarmed/talisman": r"unarmed|talisman",
 "spell:fire": r"fire|ignite|burn", "spell:cold": r"\bcold\b|freez|chill|frost|ice", "spell:lightning": r"lightning|shock|electro|spark",
 "spell:chaos": r"chaos|wither|decay|contagion", "spell:physical": r"physical|bleed|impale",
 "minion": r"minion|companion|zombie|skeleton|spectre|undead|summon", "totem": r"totem", "trap/mine": r"\btraps?\b|mine",
 "ailment:ignite": r"ignite", "ailment:shock": r"shock|electrocut", "ailment:freeze/chill": r"freez|chill",
 "ailment:poison": r"poison", "ailment:bleed": r"bleed|blood loss", "ailment:impale": r"impale",
 "curse/mark": r"curse|hex|\bmark", "herald/aura/buff": r"herald|aura|presence|buff|persistent|spirit",
 "warcry": r"warcry", "charges/resources": r"charge|rage|glory|valour|darkness|infusion|combo|flask|charm",
 "defence": r"armour|evasion|energy shield|block|ward|guard|resist|recoup|leech|deflect|life regen",
 "on-death/corpse": r"corpse|on death|on kill|killed|when .* dies|explode|remnant",
}
FAMRE = {k: re.compile(v, re.I) for k, v in FAM.items()}

def lines():
    d = json.load(open(CAT))
    for u in d["uniques"]:
        for l in u["lines"]:
            yield ("unique", u.get("name") or u["base"], l["text"])
    for n in d["notables"]:
        for s in n["stats"]:
            yield ("asc:" + n["ascendancy"] if n["ascendancy"] else "notable", n["name"], s)
    for k in d["keystones"]:
        for s in k["stats"]:
            yield ("keystone", k["name"], s)
    for s in d["supports"]:
        yield ("support", s["name"], s.get("description") or "")
    for s in d["skills"]:
        yield ("skill", s["name"], s.get("description") or "")
    for x in json.load(open(NEW)):
        for part in re.split(r"(?<=[.;])\s+", x["text"]):
            yield ("1.0:" + x["kind"], x["name"], part)

def main(out):
    hits = []
    table = collections.Counter()
    for src, name, text in lines():
        if not text: continue
        prims = []
        for p, (pos, neg) in PRIMS.items():
            if pos.search(text) and not (neg and neg.search(text)):
                prims.append(p)
        if not prims: continue
        fams = [f for f, r in FAMRE.items() if r.search(text) or r.search(name)]
        if src.startswith("asc:"):
            fams.append("asc:" + src[4:])
        hits.append({"src": src, "name": name, "text": text, "prims": prims, "fams": fams})
        for p in prims:
            for f in fams or ["(none)"]:
                table[(f, p)] += 1
    json.dump(hits, open(out, "w"), indent=0)
    fams = sorted({f for f, _ in table})
    ps = list(PRIMS)
    print("family".ljust(28) + " ".join(p[:3] for p in ps))
    for f in fams:
        print(f.ljust(28) + " ".join(str(table[(f, p)]).rjust(3) for p in ps))
    print("total hit lines", len(hits))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/dev/null")
