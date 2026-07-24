#!/usr/bin/env bash
# Regenerate every image in docs/img/ from source.
#
#   ./scripts/render_figures.sh
#
# Requires Google Chrome (headless screenshots) and the project venv on PATH.
# The terminal figure re-runs the real scanner, so the output in the image is
# always whatever the code actually prints today.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIG="$REPO/scripts/figures"
OUT="$REPO/docs/img"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
PY="${PYTHON:-python3}"

mkdir -p "$OUT"

shot() { # shot <src.html> <out.png> <width> <height>
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
            --force-device-scale-factor=2 --window-size="$3,$4" \
            --screenshot="$OUT/$2" "file://$1" 2>/dev/null
  echo "  → docs/img/$2  (${3}x${4} @2x)"
}

echo "Rendering figures…"
"$PY" "$FIG/make_terminal.py" >/dev/null

shot "$FIG/hero.html"                     hero.png          1200 600
shot "$FIG/architecture.html"             architecture.png  1200 700
shot "$FIG/lineage.html"                  lineage.png       1200 700
shot "$FIG/terminal.html"                 scan.png           940  893
shot "$FIG/report_frame.html"             report.png        1120 1568

echo "Done."
