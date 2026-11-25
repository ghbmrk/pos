"""Feedback-loop finder over rule text.

Nodes are quantities (resources, counts, stats). A rule line that mentions a
generator verb links every quantity in its condition/scaler part to every
quantity in its gain part. Cycles of length <= 3 are printed with the lines
that make each edge; at least one edge must come from a 1.0 entry.
Heuristic: it over-generates; triage reads the lines.
"""
import json, re, itertools, collections, sys
sys.path.insert(0, "tools/adversarial")
from scan import lines

Q = {
 "darkness": r"darkness", "rage": r"\brage\b", "glory": r"glory", "valour": r"valour",
 "frenzy": r"frenzy charge", "power_charge": r"power charge", "endurance": r"endurance charge",
 "flame": r"sacrificial flame|infernal flame|demonflame", "combo": r"\bcombo\b",
 "minion_count": r"minions?\b(?! deal)|zombie|skeleton|foul eye|shade|mirage|afterimage|clone|totem",
 "minion_life": r"minion'?s? (maximum )?life|life of the (supported )?minion",
 "remnant": r"remnant", "infusion": r"infusion", "corpse": r"corpse",
 "kill": r"\bkill|killed|dies|on death", "crit": r"critical hit", "hit_count": r"\bhits?\b",
 "trigger": r"trigger", "cooldown": r"cooldown", "stealth": r"stealth|ambush",
 "self_damage": r"take .*damage|lose .*life|sacrifice", "life": r"maximum life|current life",
 "mana": r"\bmana\b", "es": r"energy shield", "spirit": r"\bspirit\b", "armour": r"\barmour\b",
 "blood_loss": r"blood loss", "bleed": r"bleed", "ignite": r"ignite", "freeze": r"freez",
 "shock": r"shock|electrocut", "poison": r"poison", "impale": r"impale", "curse": r"curse",
 "enemy_power": r"\bpower\b(?! charge)", "projectile": r"projectile|knives", "stage": r"\bstages?\b",
 "flask": r"flask", "charm": r"charm", "guard": r"\bguard\b", "empower": r"empower",
 "buried_blade": r"buried blade", "wind_blade": r"wind blade", "bell": r"\bbells?\b",
 "frenzy_any": r"charges?\b",
}
QR = {k: re.compile(v, re.I) for k, v in Q.items()}
GEN = re.compile(r"\b(gain|grant|generate|create|summon|trigger|recover|regenerate|refresh|add|accumulat|build|stor|consume .* to|when|on |per |for each|equal to|based on)", re.I)

GENERIC = {"hit_count","trigger","kill","crit","mana","life","cooldown","frenzy_any","es"}
import os
KEEP_GENERIC = os.environ.get("LOOPS_GENERIC") == "1"
def qs(t): return {k for k, r in QR.items() if r.search(t) and (KEEP_GENERIC or k not in GENERIC)}

edges = collections.defaultdict(list)
for src, name, text in lines():
    if not GEN.search(text): continue
    m = re.split(r"\b(when|whenever|on |per |for each|for every|if |while |after |equal to|based on)\b", text, maxsplit=1, flags=re.I)
    if len(m) < 3: continue
    gain, cond = m[0], m[1] + m[2]
    a, b = qs(cond), qs(gain)
    for x in a:
        for y in b:
            if x != y: edges[(x, y)].append((src, name, text))
adj = collections.defaultdict(set)
for (x, y) in edges: adj[x].add(y)
is10 = lambda es: any(e[0].startswith("1.0") for e in es)
out = []
for x in list(adj):
    for y in list(adj[x]):
        if x in adj.get(y, ()) and x < y:
            out.append([x, y, x])
        for z in list(adj.get(y, ())):
            if z not in (x, y) and x in adj.get(z, ()) and x < y and x < z:
                out.append([x, y, z, x])
res = []
for cyc in out:
    es = [edges[(cyc[i], cyc[i+1])] for i in range(len(cyc)-1)]
    if os.environ.get("LOOPS_ALL") != "1" and not any(is10(e) for e in es): continue
    res.append((cyc, es))
print(len(res), "cycles touching 1.0")
for cyc, es in res:
    print("\n##", " -> ".join(cyc))
    for (a, b), e in zip(zip(cyc, cyc[1:]), es):
        e10 = [x for x in e if x[0].startswith("1.0")]
        pick = (e10 or e)[:2]
        for s, n, t in pick:
            print(f"  {a}->{b} [{s}] {n}: {t[:150]}")
