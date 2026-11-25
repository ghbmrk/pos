import os
HERE=os.path.dirname(os.path.abspath(__file__))
"""Census: pair every 1.0 addition (new_1_0.json, poe2db 2026-11-25) with every pinned-catalogue rule sharing a mechanic hook.
Writes pairs_1_0.json (score, new, kind, old, shared hooks, old text). Lexical: a candidate list for hand triage, not a verdict.
"""
import json,re,math,collections
new=json.load(open(os.path.join(HERE,'new_1_0.json')))
c=json.load(open(os.path.join(HERE,'..','..','data','catalogue','601768b.json')))
old=[]
for n in c['keystones']: old.append(('keystone',n['name'],' | '.join(n['stats'])))
for n in c['notables']:
    old.append(('asc:'+n['ascendancy'] if n.get('ascendancy') else 'notable',n['name'],' | '.join(n['stats'])))
for u in c['uniques']:
    nv=len(u.get('variants') or [])
    lines=[l['text'] for l in u['lines'] if not l.get('variants') or nv in l['variants']]
    old.append(('unique',u['name'],' | '.join(lines)))
for s in c['supports']: old.append(('support',s['name'],s.get('description') or ''))
for s in c['skills']: old.append(('skill',s['name'],s.get('description') or ''))
newnames={e['name'].lower() for e in new}
old=[o for o in old if o[1].lower() not in newnames and o[2]]
HOOKS={
'frenzy':r'frenzy charge','power_charge':r'power charge','endurance':r'endurance charge','charge_consume':r'consum\w* (a |all |your )?\w* ?charges?|charges? consumed',
'rage':r'\brage\b','glory':r'\bglory\b','valour':r'valour','darkness':r'darkness','stealth':r'stealth|ambush','shade':r'\bshades?\b',
'empower':r'empower','ancestral':r'ancestral(ly)? boost','warcry':r'warcr','strike':r'\bstrikes?\b','slam':r'\bslams?\b|aftershock','channel':r'channel',
'trigger':r'\btrigger','cooldown':r'cooldown','combo':r'\bcombo\b','parry':r'parr','ready_stance':r'ready stance|blood stance|sand stance',
'bleed':r'bleed','blood_loss':r'blood loss','ignite':r'ignit','poison':r'poison','chill_freeze':r'\bchill|\bfreez|frozen','shock':r'shock|electrocut',
'impale':r'impal','armour_break':r'break\w* armour|armour break|broken armour','curse':r'\bcurse|hex','mark':r'\bmarks?\b','minion':r'minion','companion':r'companion',
'zombie':r'zombie|undead','spectre':r'spectre','totem':r'totem','trap':r'\btraps?\b','remnant':r'remnant','ground':r'ground surface|ignited ground|shocked ground|chilled ground|blood pool',
'wind':r'\bwind\b|whirlwind|tailwind','buried_blade':r'buried blade','sand':r'sand disk|sand-ingrained|\bsand\b','projectile':r'projectile','self_damage':r'take \w* ?(fire|physical|chaos)? ?damage|sacrific|life spent|life cost',
'life_loss':r'lose life|life loss','power_enemy':r'\bpower of|enemy power|per power|monster power','presence':r'presence','banner':r'banner|standard',
'shapeshift':r'shapeshift','infusion':r'infusion','spirit_res':r'\bspirit\b','block':r'\bblock','guard':r'\bguard\b','crit':r'critical','weapon_swap':r'weapon set|weapon swap',
'dual_wield':r'dual wield','two_hand':r'two hand|two-hand','dagger':r'dagger','sword':r'\bswords?\b','mace':r'\bmaces?\b','quarterstaff':r'quarterstaff','spear':r'\bspear',
'max_life':r'maximum life','energy_shield':r'energy shield','armour':r'\barmour\b','fire_taken':r'fire damage taken|taken as fire','recoup':r'recoup','leech':r'leech',
'heavy_stun':r'heavy stun|primed','immobilise':r'immobilis|pin\b','extra_dmg':r'as extra',
'meta_gem':r'meta|socketed spell','concentration':r'concentration','decay':r'decay','volatility':r'volatil','exposure':r'exposure','penetrat':r'penetrat',
'duration':r'skill effect duration|buff duration','echo_repeat':r'repeat|echo|afterimage|mirage|copy|copies','anvil_bell':r'anvil|bell',
}
STRONG=re.compile(r'\bmore\b|as extra|per |count as|counts as|double|instead|no limit|cannot be|always|infinite|not consume|not count|without|twice|additional',re.I)
def hooks(t):
    t=t.lower(); return {h for h,p in HOOKS.items() if re.search(p,t)}
oh=[(o,hooks(o[2])) for o in old]
df=collections.Counter(h for _,hs in oh for h in hs)
N=len(oh)
idf={h:math.log(N/(1+df[h])) for h in HOOKS}
generic={'crit','armour','max_life','energy_shield','duration','projectile','trigger','cooldown','extra_dmg','presence','block','spirit_res'}
pairs=[]
for e in new:
    nh=hooks(e['name']+' '+e['text'])
    e['hooks']=sorted(nh)
    for o,hs in oh:
        sh=(nh&hs)-generic
        if not sh: continue
        s=sum(idf[h] for h in sh)*(1.5 if STRONG.search(o[2]) else 1.0)
        pairs.append((round(s,2),e['name'],o[0],o[1],sorted(sh),o[2][:260]))
pairs.sort(reverse=True)
json.dump(pairs,open(os.path.join(HERE,'pairs_1_0.json'),'w'))

print('old entries',N,'pairs',len(pairs))
per=collections.Counter(p[1] for p in pairs if p[0]>=6)
print(per.most_common(40))
