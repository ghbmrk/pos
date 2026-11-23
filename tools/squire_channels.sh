#!/usr/bin/env bash
# Joint player+Squire search for every Squire value channel (docs/squire-channels.md). ASSUMED what-if runs.
# Usage: tools/squire_channels.sh OUT_DIR [workers]   then: python tools/squire_channels.py OUT_DIR
set -euo pipefail
out=${1:?out dir}; w=${2:-4}
cd "$(dirname "$0")/.."
for f in examples/squire_channels/*.yaml; do
  sc=$(basename "$f" .yaml)
  [ -f "$out/$sc/run.json" ] && { echo "skip $sc (done)"; continue; }
  echo "== $sc $(date -u +%H:%M:%S)"
  python -m pos_pipeline run "$f" weapon='Akoyan Spear' body_armour='Wyrmscale Coat' helmet='Wrapped Greathelm' \
    gloves='Vaal Wraps' boots='Wrapped Sandals' --assumed --workers "$w" --out "$out/$sc" > "$out/$sc.log" 2>&1 || echo "FAILED $sc (see $out/$sc.log)"
done
