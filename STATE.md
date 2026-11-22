# Path of Sim: state

## Decisions
<!-- YYYY-MM-DD · decision · approval message id -->
- 2026-11-22 · Ground project in a new GitHub repo; STATE.md moves into it once attached · cmsg_01RxGYnd78N9kMbbAJ5pWDhU2XyFQrMKmkyZcGtoRYvRTr
- 2026-11-22 · Goal: PoE2 build simulator: natural-language build idea -> variants (items etc.) tested in parallel at expected gear price points; grounded in real PoB calcs, ready to update for PoE2 1.0 · cmsg_01RxGYnd78N9kMbbAJ5pWDhUSxYwkAYM47GpUS3ZLtLqCT
- 2026-11-22 · Fable 5.2 is advisor; each recommendation card gets a fresh Fable review thread before posting · cmsg_01RxGYnd78N9kMbbAJ5pWDhUMM6wQFWQmvRketaudBWyHq
- 2026-11-22 · Alerts thread retired; blockers go to Decisions; standing Questions thread (Opus) added · cmsg_01RxGYnd78N9kMbbAJ5pWDhUEwwmv9Me7Q9YyXKfpxtwhV
- 2026-11-22 · PoB calcs: fork MaxWilk/poe2-build-mcp engine layer (MIT), re-pin to current PoB-PoE2 dev in a timeboxed spike first; if it breaks badly, switch to own wrapper on HeadlessWrapper.lua. Variant + price orchestration built in-house. See docs/prior-art.md · cmsg_01RxGYnd78N9kMbbAJ5pWDhUAkFQ7SB2ZY4Cm3XN5SYSps
- 2026-11-22 · Gear price tiers: Option 4 hybrid (point budgets over mod ranks + premium weights, price-capped trade anchors, uniques via poe.ninja/bands); docs/price-tiers.md · cmsg_01RxGYnd78N9kMbbAJ5pWDhU459EKgtfBKKEj26VPNCE18

## Open work
<!-- id · state · owner thread -->
- D1 · standing · Decisions 1 (cmsg_01RxGYnd78N9kMbbAJ5pWDhULpAd6m9DDdnmdwnR4WgH67)
- A1 · retired · Alerts 1 (blockers go to Decisions)
- Q1 · standing · Questions 1 (Opus)
- S2 · done (PR open) · re-pin spike: result STAY ON FORK; engine layer in pos_engine/, PoB-PoE2 submodule at 601768b, zero patches; docs/engine-fork.md · thread "Test updating the PoB engine fork"
- R1 · done · ghbmrk/pos scaffolded (README, .gitignore), STATE.md moved into repo · thread "Set up the pos repo"
- S1 · done · prior-art memo docs/prior-art.md + reuse-vs-build decision · thread "Evaluate existing PoE2 build tools" (cmsg_01RxGYnd78N9kMbbAJ5pWDhUXjKQcaEQwYS7APh7ozgeRB)
- P1 · done (PR open) · data/tiers.yaml + pos_tiers/ (tier table, ModItem rank resolver, PriceModel/AnchorSumModel, hand-set unique bands) + .github/workflows/tests.yml; anchors empty until sampled; poe.ninja fetch (price-tiers step 4) still blocked · thread "Build gear tier tables and pricing"
- S3 · done · rare-item price tiers decided (docs/price-tiers.md, PR #2 merged) · thread "Plan rare-item price tiers"
- G1 · done (PR open, NL-front card pending) · pipeline design docs/pipeline.md · thread "Design build idea to variants pipeline" (cmsg_01RxGYnd78N9kMbbAJ5pWDhU83mMm33bteTmbpNC7yECs2)
- G2 · startable · catalogue export from pinned PoB + resolve() (Sonnet) · see docs/pipeline.md
- G4 · startable · engine pool + SQLite cache + large-build benchmark (Sonnet)
- G3 · blocked on G2 · BuildSpec schema, validator, assembler, PoB-code import (Sonnet)
- G5 · blocked on G3, G4 · support search (Sonnet)
- G6 · blocked on G3, G4 · tree stage via optimize_passives (Sonnet)
- G7 · blocked on G3, G4 · gear search within tier budgets (Sonnet)
- G8 · blocked on G5-G7 · orchestrator, report, CLI, golden e2e (Sonnet)
- G9 · blocked on G8 and NL-front decision · MCP server + usage guide (Sonnet; Opus reviews tool text)
- G10 · blocked on G2, G3; run at 1.0 (2026-12-11) · repin.sh, catalogue diff, spec revalidation (Sonnet)

## Standing rules learned
- Recommendation cards: request a Fable review thread via coordinator first.
- PRs that record or implement something the owner already decided or approved are merged without asking · cmsg_01RxGYnd78N9kMbbAJ5pWDhUYLuCFUWcofw67uLDKo4gM3
