# Idea slate validator (I3)

`python -m pos_pipeline slate validate slate.yaml` (exit 0 only if at least one candidate is kept and there is no slate-level error). Code: `pos_pipeline/slate.py`; thresholds and archetype vocabularies: `data/ideation.yaml`. Design: `docs/ideation.md`. Deterministic, no engine.

Schema: `slate: 1`, `pob_sha`, `prompt`, `brief {benchmarks, tiers, constraints, floors}`, `candidates[] {name, archetype {delivery, damage, defence, engine}, spec (BuildSpec), key_pieces [{kind, id}], claims [{text, cites [{kind, id, quote}]}], source}`. Unknown keys are structural errors (`SlateError`); a malformed `spec` block rejects only that candidate.

Per-candidate gates (errors reject the candidate; later gates only see survivors):
| gate | code(s) |
|---|---|
| BuildSpec validation (`docs/spec.md`), paths prefixed `candidates[i].spec.` | as `validate` |
| key pieces: 1-3, kind in keystone/notable/unique/support, exact catalogue resolution, fixed in the spec | `key_pieces`, `unresolved`, `key_piece_not_in_spec` |
| claims: no digits, `%` or number words (`data/ideation.yaml`); at least one cite | `claim_number`, `claim_uncited` |
| cites resolve exactly (suggestions shown, never applied); quote (>= 12 chars) is a case/whitespace-normalised substring of `pos_catalogue.query.texts(kind, entry)` | `unresolved`, `claim_no_text`, `quote_short`, `quote_mismatch` |
| rankability: main skill has a metric in `data/metrics.yaml` (an explicit `maximise` does not waive it) | `no_metric` |
| diversity: archetype vector (class/ascendancy, delivery, damage, defence, main skill, key-piece set); a candidate must differ from every earlier kept one on >= 2 fields | `near_duplicate` |
| cap: at most `max_kept` (8) kept | `over_cap` |

`delivery` and `damage` are derived from the catalogue skill types (a fixed support requiring `SummonsTotem`/`Trappable`/`Mineable` makes the delivery totem/trap/mine); a declared value that disagrees is a warning and the derived value is used. `defence` is the typed label (default `unspecified`).

Slate-level errors: `pob_sha`, brief benchmark/tier ids, `too_few` (< 3 candidates), duplicate candidate names, and `coverage` (kept candidates must span >= 3 distinct `delivery` or `damage` values unless the brief fixes both in `constraints`).

Limits (judgement): the number-word list is lexical, so a claim can still smuggle a quantity in prose it does not cover; the quote check proves the text exists in PoE2 data, not that the claim follows from it (ablation, I4/I5, tests that); `defence` is not verified against the spec.
