"""Term-driven avenue map.

Takes the mechanic words in 1.0 skill/unique descriptions (capitalised
keywords and [Bracketed|Links] from poe2db text), then finds every rule line in
the whole pinned game that mentions the same word. Each term gets: 1.0 lines
(where it appears in new content) and old lines split into producers (line
creates/applies/grants the term) and payoffs (line scales or triggers from it).
"""
import json, re, sys, collections
sys.path.insert(0, "tools/adversarial")
from scan import lines

STOP = set("""Attack Attacks Skill Skills Spell Spells Damage Hit Hits Level Requires Tier Cost Mana Cooldown Time
AoE Melee Strike Strikes Trigger Triggered Triggers Duration Physical Fire Cold Lightning Chaos Support Supported Supports
Category Requirements Str Dex Int Speed Max Projectile Projectiles Sword Dagger Mace Bow Spear Unique Rare Life Minion Minions
Grants Gain Deals Persistent Buff Elemental Damaging Enemies Enemy The When This If Your You Using Creates Additional
Channel Channelling Sustained Travel Payoff Conditional Staged Nova Wind Slam Trap Traps Remnant Remnants Base Weapon Armour
Two Hand One Edit Effects From Quality Each Hitting Supported Can Cannot Has Have Any All Allies Ally Shield Body Helmet Boots
Gloves Belt Ring Amulet Quarterstaff Wand Staff Sceptre Longsword Damage Rating Critical Chance Bonus Charm Slot Slots Requires:
Converts Explosion Explodes Hand Seconds Second""".split())
PHR = re.compile(r"\[([A-Za-z]+)\|([^\]]+)\]|\b((?:[A-Z][a-z'\-]+)(?:\s+(?:of\s+)?[A-Z][a-z'\-]+)*)")
PROD = re.compile(r"\b(gain|grant|create|inflict|apply|applies|cause|leave|summon|trigger|build|put|enter)", re.I)

def main():
    new = json.load(open("tools/census/new_1_0.json"))
    terms = collections.Counter()
    where = collections.defaultdict(set)
    for x in new:
        for m in PHR.finditer(x["text"]):
            t = (m.group(2) or m.group(3) or "").strip()
            if not t or t in STOP or len(t) < 4 or t.split()[0] in STOP: continue
            if t == x["name"] or t in x["name"]: continue
            terms[t] += 1; where[t].add(x["name"])
    old = [l for l in lines() if not l[0].startswith("1.0")]
    rows = []
    for t, n in terms.items():
        r = re.compile(r"\b" + re.escape(t.rstrip("s")) + r"s?\b", re.I)
        hits = [l for l in old if r.search(l[2])]
        prod = [l for l in hits if PROD.search(l[2].split(t)[0] if t in l[2] else l[2])]
        rows.append((t, sorted(where[t]), hits, prod))
    rows.sort(key=lambda r: -len(r[2]))
    for t, w, hits, prod in rows:
        print(f"\n## {t} | 1.0 users: {', '.join(w)[:160]} | old lines: {len(hits)} (producers {len(prod)})")
        for s, nm, tx in hits[:int(sys.argv[1]) if len(sys.argv) > 1 else 6]:
            print(f"   [{s}] {nm}: {tx[:170]}")

if __name__ == "__main__":
    main()
