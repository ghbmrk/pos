# Catalogue text and ideation queries (I2)

The catalogue export (schema 2) now carries the PoE2 text that ideation claims must quote, so these queries run without an engine.

## New fields
- `skills[]` / `supports[]`: `description` (gem description from PoB skill data; 964 of 966 gems have one).
- `uniques[]`: `lines` (mod lines in file order, header lines and `{tags:..}`/`{range:..}` prefixes stripped; each `{text, implicit?, variants?}`), `variants` (names from `Variant:` headers, 1-based in `lines[].variants`), `req_level`.
  Unique text is exported as written in PoB's data, ranges unrolled (`(10-20)%`). Variant lines for old patches stay; `explain` and `search` use the newest variant (last `Variant:`).
- Not exported: per-level gem stat values (stat ids, not text) and flavour text.

## Queries (`pos_catalogue.Catalogue` methods, same functions in `pos_catalogue/query.py`)
| call | CLI | returns |
|---|---|---|
| `search(kind, text=, skill_types=, tags=, ascendancy=, class_=, limit=)` | `python -m pos_catalogue search KIND [text...] [--skill-type T] [--tag T] [--ascendancy A] [--class C] [--limit N]` | entries; all filters AND; each text term must start a word in name or text |
| `enablers(skill_type)` | `... enablers TYPE` | `supports_adding` (add_types include it) + keystones/notables/uniques whose text names it |
| `bridges(a, b, limit=)` | `... bridges A B` | per kind, entries mentioning both terms |
| `explain(kind, id)` | `... explain KIND ID` | quotable `text` lines plus structure (support type rules, unique base/slot/variants/all_lines) |

`texts(kind, entry)` is the single definition of "quotable text" (keystone/notable stats, newest-variant unique lines, gem description, base implicit); the I3 citation check should call it.

Matching is word-start, case-insensitive: `fire` matches "Fireball", not "Misfire". It is lexical, not semantic: a bridge for "Armour" and "Energy Shield" finds co-occurrence, the LLM judges whether it is a good idea.

## Re-pin
`pos_repin` diffs every non-name field, so changed unique lines or gem descriptions appear as `lines` / `description` under "changed" without code changes (test added). `tools/repin.sh` re-exports the catalogue; the pinned-export test fails until it is committed.
