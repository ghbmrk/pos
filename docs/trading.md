# Currency trading automation: scope and decision boundary

Status: exploration, no build. Requested 2026-11-23 (cmsg_01RxGYnd78N9kMbbAJ5pWDhULmFRj549pWy1JwefntjCdc). Goal under review: accumulate currency in the 1.0 economy with automated help.

## Facts (checked 2026-11-23)

### Rules and access

Primary sources: GGG [Terms of Use](https://www.pathofexile.com/legal/terms-of-use-and-privacy-policy), [developer docs](https://www.pathofexile.com/developer/docs) and [API reference](https://www.pathofexile.com/developer/docs/reference), [poe.ninja API docs](https://poe.ninja/docs/api).

- **ToU 7(3)** forbids "any automated software or 'bots' in relation to your access or use of the Website, Materials or Services"; **7(6)** forbids "data gathering and extraction tools ... to extract information from the Website"; **7(5)** forbids connecting to servers through anything but the game client; **7(9)** forbids reverse engineering protocols. Breach "immediately terminates the Licence" (cl. 6); GGG may close the account without notice (cl. 17).
- **ToU 23** permits trading via in-game mechanisms "and through use of official Grinding Gear Games Website APIs". The trade site's search/fetch/live-search endpoints are **not** in the API reference, and the docs say only documented resources are supported. Automated use of them therefore falls under 7(3)/7(6), whatever the rate.
- **Macros** (developer docs): allowed only when "invoked manually by the user", one action per invocation (one chat message or command counts as one action); no timers or file-change triggers. An auto-whisper on a new listing fails both conditions.
- **Official Currency Exchange data exists and is public**: `GET https://web.poecdn.com/api/currency-exchange/poe2[/<id>]`, per-pair hourly digests of completed trades, "purely historical", no current hour. No OAuth scope listed. New OAuth app registration is closed ("unable to process new applications"). Rate limits come in `X-Rate-Limit-*` headers and are "dynamic".
- **poe.ninja** supports only its economy overview endpoints (PoE2 exchange overview and unique item overviews), hourly for PoE2, ~5 min cache, descriptive User-Agent with contact, excessive clients blocked, no stability guarantee.
- **Enforcement evidence is anecdotal.** Forum thread [3572697](https://www.pathofexile.com/forum/view-thread/3572697) (2024): a Live Search buyer banned for "Third party software", first ban revoked on appeal; GGG staff declined to discuss. No GGG statement on live search found.
- Network: this cloud environment reaches poe.ninja but not `web.poecdn.com`, pathofexile.com or poe2scout.com (proxy refusal, 2026-11-23).

### The X summary, claim by claim

All eight named repositories exist (READMEs fetched from raw.githubusercontent.com; stars and last-commit dates not checked, GitHub API is out of scope for this session).

| Claim | Verdict | Evidence |
|---|---|---|
| vanzan01/poe2scout-mcp: 11 tools, rate-limited, currency-focused, built for Claude Code | True. "Arbitrage-oriented" is overstated: tools are price history, trend/volatility signals, leagues, uniques; no arbitrage tool. Calls `poe2scout.com/api/*`, which poe2scout now calls a *temporary* compatibility proxy (canonical host `api.poe2scout.com`). MIT. | README |
| sergeyklay/poe2-mcp-server: public APIs only, no accounts | True. Currency, item prices, exchange tops (poe.ninja, poe2scout), wiki, poe2db, PoB decode/compare. MIT. | README |
| PartyPenguin/ExileOracle: stash, gear, price checks | True, but needs the user's `POESESSID` cookie copied from the browser. MIT. | README |
| zgrummons/pob2-mcp: trade search + arbitrage calculator | True. Trade tools are off by default and need `POESESSID` (README: "Cloudflare/session-gated"). GPL-3.0, so code reuse would relicense `pos`. | README |
| GlacianNex/POE2MarketMCP: local SQLite collector, history, multi-step arbitrage | True. Currency from poe.ninja hourly; optional listings and exchange sweeps use GGG's trade API; no cookie for public listings; listing tools return whisper text for a human to paste. MIT. | README |
| merlin293/PoE2-Live-Search-Sniper: auto-whisper bot | True. Its own README: "strictly against Path of Exile's Terms of Service ... significant risk of account suspension or permanent ban". | README |
| Overlays (Exiled Exchange 2 etc.) are the safe daily tool | Mostly true; clipboard based. Note forum thread 3777565 reports a ban attributed to EE2 (unverified cause). | README, forum |

### What the data can and cannot show

Measured on poe.ninja's PoE2 exchange overview (`/poe2/api/economy/exchange/current/overview`, league Rise of the Abyssal, 36 currencies, fetched 2026-11-23):

- **No cross-rate arbitrage is visible in poe.ninja data, by construction.** Each currency carries one value in divines plus its single highest-volume pair rate. Recomputing each value through that pair matches the published value to a median 0.02% (max 0.33%). The numbers are a single-numeraire projection, so a triangle (chaos -> exalted -> divine -> chaos) always closes. Multi-step arbitrage detection needs per-pair data: GGG's public Currency Exchange digests (hourly, per pair) or the in-game order book. Hourly digests are an hour stale, so they show *where* spreads were, not executable quotes.
- **Directional moves are large.** Seven-day change among the 12 highest-volume currencies ranged from -19% (divine, in chaos terms) to +184% (perfect jeweller's orb); exalted +79%, annul +57%. This is the end of a league (thin, drifting market), so it overstates a mid-league week; league-start weeks are more volatile still.
- **Edge per tier is not measurable from public data.** No primary source reports trader returns. Estimates below are reasoning, labelled as such.

## Tiers and the line

| Tier | What | ToS / ban risk | Plausible edge (estimate) |
|---|---|---|---|
| 0. Market intelligence | Collect public aggregates (poe.ninja hourly, GGG per-pair exchange digests) into history; trend, volatility, volume filters; LLM reads via MCP | None found: documented, public endpoints | Indirect: avoids selling under value and buying spikes. Main value is pricing, not profit. |
| 1. Decision support, manual execution | Ranked signals: league-start trends (what rises as crafting demand arrives), spread between pair digests, items cheap vs history; human places Currency Exchange orders or whispers | None: all in-game actions are manual | The only tier with real edge for one player. Exchange limit orders capture the spread with no automation; early-league speculation on predictable demand is where most currency is made. Order of magnitude: a few percent per cycle on liquid pairs; larger, riskier on early-league trends. |
| 2. Automated trade-site reads | Polling trade-site search/live search with `POESESSID`, alerts to a human | High in principle, enforcement uneven: automated use of undocumented Website endpoints breaches ToU 7(3)/7(6) at any rate, and runs under the account's session | Small over tier 1 for currency (the Exchange already pools currency liquidity); matters for underpriced gear, which is a different goal. |
| 3. Automated execution | Auto-whisper, sniping, input automation in the client | Highest: breaches 7(3) and the macro rule; the sniper's own README says so. Account loss erases the gain. | Largest gross edge on mispriced listings, but a ban takes the account and its stash. |

**Decision boundary.** Tiers 0-1 read only documented public data and leave every in-game action to the player. Tier 2 is the first that automates against undocumented Website endpoints (ToU 7(3)/7(6)); tier 3 also acts in game. The line follows one test: *does software use the account's session or act in game?* If no, it is in bounds.

## Recommendation

1. Draw the line between tiers 1 and 2. Build nothing that holds `POESESSID` or sends whispers.
2. Do not build a collector. Reuse GlacianNex/POE2MarketMCP (MIT, local SQLite history, poe.ninja hourly) with its trade-API watchlist/sweep/listing options left off (they call undocumented trade endpoints), run on the owner's device; add sergeyklay/poe2-mcp-server (MIT, no accounts) for ad-hoc questions. vanzan01/poe2scout-mcp is a fallback only, because it targets poe2scout's temporary API path.
3. Fit with this repo: the same price history is what `pos_tiers` needs for unique prices and currency-to-divine conversion (docs/price-tiers.md step 4, still empty). One `data/prices/` snapshot importer from poe.ninja's exchange overview serves both; keep the trading goal outside `pos` so the build simulator stays one task.
4. Timing: the 1.0 reset (2026-12-11) empties every history. Start the collector on launch day; signals are meaningless for the first 24-48 h of data, which is also when most currency is made by playing and selling early drops. The 2026-12-12 repin reminder is the natural start point.
5. Measure before scaling: log every manual trade (paid, received, divine value at the hour) for the first 1.0 week. If logged edge does not beat time spent mapping, stop at tier 0 as a pricing aid.

## Open questions (not blocking)

- Exact fields of GGG's per-pair Currency Exchange digests (public endpoint, but unreachable from this environment); add it to the collector if POE2MarketMCP does not already read it.
- Whether this cloud environment should be allowed to reach poe2scout.com (currently blocked); not needed if the collector runs on the owner's device.
