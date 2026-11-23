# Meta lessons: past metas as ideation priors

Owner requirement (2026-11-23, cmsg_01RxGYnd78N9kMbbAJ5pWDhUX2GMWf6TSLPYKzmKmpb39v): ideas for meta-competitive builds
should be informed by lessons from previous meta builds across PoE1 and PoE2, feeding the high-level to granular idea
step. Design principle that filters them (cmsg_01RxGYnd78N9kMbbAJ5pWDhUMPY2hjQhYp2yGeFZAi2wG1): a build's core
interaction must compound; marginal gains are not enough.

## What ships

| Piece | Role |
|---|---|
| `data/meta_lessons.yaml` | 17 abstract patterns: mechanism, why it compounds, limits, eras + evidence, PoE2 anchors, probe levers, PoB coverage |
| `pos_pipeline/meta_lessons.py` | `render()` (prompt block), `public()` (no example names), `validate()` |
| `pos_mcp/ideate.py` | new Step 1b "Priors from past metas": patterns as generators; engine = 2+ patterns that feed each other |
| `pos_pipeline/slate.py` | `archetype.patterns: "id+id"`; unknown id = error `unknown_pattern`; fewer than 2 = warning `engine_not_compounding` |
| MCP `meta_lessons(pattern)` | full entries (eras, evidence, anchors, levers), never the example names |
| `tools/meta_snapshot.py` | dated poe.ninja build-index snapshot into `data/meta/` (evidence) |

## Patterns, not names

Past metas are mostly PoE1, and PoE1 names are the main hallucination source the slate gate catches (I7 caught PoE1 skill
names at resolve in its slates, docs/ideation-eval.md). So each pattern is written game-agnostically, and its PoE2 presence is given only as
catalogue names that resolve `exact` on the pinned data (test). Past build names stay in `examples` for provenance and
a test proves none reaches the prompt or the MCP tool. A pattern with no PoE2 path (`persistent_dot_aura`: no burning
aura skill in pin 601768b) is kept for 1.0 but not rendered.

The label does not prove compounding; the engine does. That is why too few patterns is a warning, not an error. L6
can turn `archetype.patterns` into the mechanism hypothesis: each pattern lists the probe levers whose shadow price
should rise if it carries the build (`levers`, ids checked against `data/probes.yaml`).

## Sources (checked 2026-11-23)

| Source | Reachable | What it gives |
|---|---|---|
| poe.ninja `/{poe1,poe2}/api/data/build-index-state` | yes | Top-10 class (PoE2) or class+skill (PoE1) shares for the current and previous leagues. Snapshot: `data/meta/ninja-2026-11-23.json` |
| poe.ninja `/{game}/api/data/index-state` | yes | League lists; old build leagues go back only about three PoE1 leagues (Mirage, Ancestors, Allflame) and one PoE2 league (Runes of Aldur) |
| poe.ninja builds pages | no | Cloudflare challenge; per-build exports not in the open API |
| pobb.in | yes | Single exports by id (the Gemling Legionnaire reference, docs/squire-channels.md); no index |
| pobarchives.com, poedb.tw, poewiki.net, web.archive.org, reddit, maxroll, mobalytics | no | Blocked by the environment proxy or Cloudflare |
| raw.githubusercontent.com | yes | No known public dataset of historical ladders |

Consequence: older eras (PoE1 2.x-3.x) rest on recalled league history, labelled `evidence: recall`. They are priors
for generating ideas, which the engine then measures; nothing is ranked on them. Sourced figures in the corpus:
Gemling Legionnaire 32% of the Forbidden Rites (PoE2 0.4) build index (stat stacking); Righteous Fire Chieftain first in
the PoE1 Covens index at 5.1% (persistent aura scaled by defence). Spirit Walker led Runes of Aldur at 28%.

To widen the evidence: allow pobarchives.com (or a poe.ninja build-export source) for the environment, then add a
`snapshot:` era per pattern from tagged exports; or rerun `tools/meta_snapshot.py` each league to accumulate shares.

## Maintenance

- Re-pin: `test_corpus_validates_on_pinned_catalogue` fails if an anchor stops resolving; fix the anchor or mark the
  pattern `absent`.
- New league: `python tools/meta_snapshot.py`, commit the file, cite it as `snapshot:data/meta/ninja-<date>.json`.
