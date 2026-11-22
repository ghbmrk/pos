# Path of Sim: state

## Decisions
<!-- YYYY-MM-DD · decision · approval message id -->
- 2026-11-22 · Ground project in a new GitHub repo; STATE.md moves into it once attached · cmsg_01RxGYnd78N9kMbbAJ5pWDhU2XyFQrMKmkyZcGtoRYvRTr
- 2026-11-22 · Goal: PoE2 build simulator: natural-language build idea -> variants (items etc.) tested in parallel at expected gear price points; grounded in real PoB calcs, ready to update for PoE2 1.0 · cmsg_01RxGYnd78N9kMbbAJ5pWDhUSxYwkAYM47GpUS3ZLtLqCT
- 2026-11-22 · Fable 5.2 is advisor; each recommendation card gets a fresh Fable review thread before posting · cmsg_01RxGYnd78N9kMbbAJ5pWDhUMM6wQFWQmvRketaudBWyHq
- 2026-11-22 · Alerts thread retired; blockers go to Decisions; standing Questions thread (Opus) added · cmsg_01RxGYnd78N9kMbbAJ5pWDhUEwwmv9Me7Q9YyXKfpxtwhV
- 2026-11-22 · PoB calcs: fork MaxWilk/poe2-build-mcp engine layer (MIT), re-pin to current PoB-PoE2 dev in a timeboxed spike first; if it breaks badly, switch to own wrapper on HeadlessWrapper.lua. Variant + price orchestration built in-house. See docs/prior-art.md · cmsg_01RxGYnd78N9kMbbAJ5pWDhUAkFQ7SB2ZY4Cm3XN5SYSps

## Open work
<!-- id · state · owner thread -->
- D1 · standing · Decisions 1 (cmsg_01RxGYnd78N9kMbbAJ5pWDhULpAd6m9DDdnmdwnR4WgH67)
- A1 · retired · Alerts 1 (blockers go to Decisions)
- Q1 · standing · Questions 1 (Opus)
- S2 · startable · re-pin spike: fork MaxWilk engine layer into pos, pin PoB-PoE2 dev as submodule, aim zero PoB patches, run golden tests; report keep-fork vs own-wrapper
- S3 · startable · decision card: rare-item price-tier model (no sanctioned trade API; inputs poe.ninja economy + GGG Currency Exchange API)
- R1 · done · ghbmrk/pos scaffolded (README, .gitignore), STATE.md moved into repo · thread "Set up the pos repo"
- S1 · done (PR #1 awaiting merge) · prior-art memo docs/prior-art.md + reuse-vs-build decision · thread "Evaluate existing PoE2 build tools" (cmsg_01RxGYnd78N9kMbbAJ5pWDhUXjKQcaEQwYS7APh7ozgeRB)

## Standing rules learned
- Recommendation cards: request a Fable review thread via coordinator first.
