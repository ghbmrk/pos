# Build plan: Oro's Sacrifice Infernal Step + Echoing Strikes (Knight)

Owner ask: cmsg_01RxGYnd78N9kMbbAJ5pWDhU8YitTiYSohyC5Z6G7yAeRh (a full gear set, ascendancy and required notables for
candidate 1 in [novel-1-0-interactions.md](novel-1-0-interactions.md)). **Untested.** Item and skill text comes from
poe2db's 1.0 pages. Passive notables come from the pinned 0.5 tree (601768b). The 1.0 tree is "a sweeping overhaul",
so the notable names below are placeholders for the effect they stand for: re-map them at the 1.0 repin. Knight node
names are poe2db's translated labels, and the point costs and connections between nodes are not public yet.

## Engine in one line

Cast Infernal Step repeatedly to stack Sacrificial Flames (F). Each flame adds 3 strikes, 15% more damage and 12% extra
fire damage. At max F, Oro's makes a Frenzy Charge every second. Spend those charges on Echoing Strikes so one long cast
is copied by 2+charges afterimages.

## Ascendancy: Knight (Duelist), recommended

| Pick | Node (poe2db 1.0 wording) | Why it is here |
|---|---|---|
| Minor | Empowered Attacks deal 20% increased damage | Echoing Strikes Empowers the next Strike; one Infernal Step cast is the whole 2+3F sequence (assumption to test) |
| Notable | Crusade node: "15% more damage when a rare or legendary enemy present, 15% less damage taken when surrounded" | Unconditional ×1.15 on bosses |
| Notable | Esteemed Mentor: Summon Squire | A second body that holds boss attention during the 10 s+ teleport lock; the Squire's gear is separate |
| Notable | Bannerlord, choose Vaal Standard | Revealed as "empowering attacks"; exact numbers unknown |
| Minors and filler | Companion damage / Armour and Evasion / Glory generation | Whatever the point layout forces |

Not picked: Righteous Bastion (Guard from blocking; a 2H sword has no shield block), Glorious Entrance (the chariot is
mobility; it adds nothing here).

**Alternative: Smith of Kitava (Warrior), if the self-burn proves to be the limit.** It removes most of the 400F fire
self-hit:
- Tantalum Alloy: +75% fire res from the body armour.
- Flowing Metal: +50% of armour applies to elemental damage.
- Forged in Flame: max fire res mods also give max cold and lightning res.
- Kitavan Engraving: 15% life.

It gives up the Knight's ×1.15, the Empowered bonus and the Squire. Decision rule: at F=10 the burn is 4,000 fire once
every 10+ s, or about 1,000 after 75% res, which normal fire res already handles. So choose Smith only if the 1.0 flame
cap turns out high (F≥20) or flames decay quickly.

## Skills and supports

| Skill | Supports | Notes |
|---|---|---|
| Infernal Step (granted by Oro's, level 19) | Elemental Focus, Close Combat II (the teleport strikes land at point blank), Fire Attunement, Elemental Penetration (1.0, 30% pen), Vampirism (1.0, Strike-only) | Avoid Ferocity: it eats the Frenzy Charges that Echoing needs. Item-granted skills can be supported in the Skills Panel |
| Echoing Strikes (sword spell, 12.8 s cooldown) | cooldown recovery or duration support if available | Cast right before a high-F Infernal Step |
| Vaal Standard (Knight banner) | – | Place it at the boss |
| Summon Squire | Squire gear set (see below) | Give it a taunt or defensive melee skill if one exists at 1.0 |
| Defensive aura or herald with spare Spirit | – | The Fallen Formation gives +60 Spirit |

Rotation:
1. Place the banner.
2. Ramp to max F with 3 to 5 short casts while pressure is low.
3. Wait for full Frenzy, which comes from Oro's at max F.
4. Cast Echoing Strikes, then one long Infernal Step.
5. Repeat when Echoing comes off cooldown, about once per cast.

## Gear (player)

| Slot | Item | Key stats |
|---|---|---|
| Weapon (2H) | **Oro's Sacrifice** (Twilight Longsword) | Fixed. "No Physical Damage", 248-384 fire, 21% attack speed, 12% extra fire per flame, Frenzy at max flames. Phys-based mods do nothing here |
| Body | Rare armour/evasion body, or **The Fallen Formation** | Fallen Formation: +60 Spirit, and allies in your Presence (the Squire) gain 22% of your armour and evasion. Rare: life, fire res, armour |
| Belt | **Molten Tenet** (Plate Belt, new) | +42% fire res, +45% of armour also applies to fire, 10% of fire damage prevented recouped as life. Makes the self-burn partly heal you |
| Helmet | Rare | Life, fire/all res, armour; Stun Threshold (you can't dodge during the lock) |
| Gloves | Rare | Attack speed, life, res; added fire to attacks |
| Boots | Rare | Movement speed, life, res |
| Amulet | Rare | +max Frenzy Charge if it rolls, % gain-as-extra fire, attack speed, life |
| Rings (2) | Rare | Fire res overcap and max fire res, attack speed, gain-as-extra fire/cold |
| Jewels | Rare (about 60 sockets reported for 1.0, secondary source) | Fire damage, attack speed, life %, armour applies to fire |
| Charms and flasks | Fire-res / thawing charm equivalents; life flask | Cover the post-cast window |
| Forgemark / Bloodmark (league crafting) | Reforge one weak suffix on the belt or amulet | The mod pool is not public; check at 1.0 |

Targets for the no-death floor (estimates):
- Fire res at 90 max if achievable (a mods are needed for that).
- Cold and lightning res 75.
- Life about 5k or more.
- Armour high enough that Molten Tenet's 45% matters.

## Gear (Squire)

The Squire is used for survival and aggro, not damage:
- Heavy armour with life rolls.
- Any one-handed weapon and shield for block.
- Fallen Formation on the player adds 22% of the player's armour to it.

Earlier exports measured Squire damage at 1 to 9%, so don't spend currency on its weapon.

## Passive notables (0.5 names, mapped to effect)

Offence. Many of these are on the Empowered and "gain as extra" axes, because Echoing makes the whole sequence
Empowered:
- Empowered damage: Internal Bleeding (30% inc Empowered), Bolstering Yell (30% inc Empowered), Explosive Empowerment
  (20%).
- Extra damage: Hail (Empowered gain 16% as extra cold), Volcanic Skin (8% extra fire, +20% fire res), Molten Being
  (5% extra fire), Cremation (18% fire pen, 6% ele as extra fire).
- Damage: Heavy Blade, Ripping Blade, Stance Breaker (25% sword damage each); Singular Purpose and Overwhelm (40% 2H
  damage, -5% attack speed); Blazing Arms; Giantslayer (25% vs rare/unique); Serrated Edges (30% attack vs
  rare/unique).
- Speed: Rapid Strike (8% melee attack speed), Sharp Sight.

Frenzy Charges set the number of afterimages (2 + charges at 50% less damage):
- Fervour (+2), Frenetic (+1), Savagery (+1), Prize of the Hunt (+1). That is 3 + 5 = 8 max charges, which gives 10
  afterimages and **×6** instead of ×3.5. This is the biggest single tree lever.

Defence:
- Heatproof (+30% armour applies to fire), Tempered Defences, Knight of Tarcus (+20% armour vs elemental, Glory).
- Resilient Soul (5% recoup), Thickened Arteries (0.5% regen).
- Unbending and Strong Chin (Stun Threshold).
- Trusted Partner (5% of hit damage taken from the Squire first).

Skip: crit. Crit chance was reportedly removed from the 1.0 tree (secondary source), and Oro's base crit is 5%.

## Expected numbers (estimates, before generic scaling)

| F | Strikes per cast | Per-strike multiplier vs F=0 | With Echoing at 8 Frenzy |
|---|---|---|---|
| 5 | 17 | ×2.8 | ×16.8 |
| 10 | 32 | ×5.5 | ×33 |
| 20 | 62 | ×13.6 | ×82 |

## Must-check at 1.0 before investing

1. Sacrificial Flame cap and decay.
2. Whether afterimages repeat the whole 2+3F sequence.
3. Whether a cast can be cancelled by dodge roll; this decides uber viability.
4. Whether the whole cast counts as Empowered.
5. Whether Infernal Step accepts supports.
6. Whether its gem level 19 requires character level 84 to use.
7. The Knight point layout.
8. Price: Oro's is new; guess 1 to 5 divines in week 1 and under 1 after about 2 weeks unless drop-restricted.
