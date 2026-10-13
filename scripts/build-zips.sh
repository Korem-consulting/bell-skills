#!/usr/bin/env bash
# Build one zip per skill for Claude.ai (Settings → Capabilities → Skills),
# which takes each skill as its own upload. Output: dist/<skill>.zip, each
# holding <skill>/SKILL.md plus that skill's references/ and scripts/.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
out="${1:-$root/dist}"
rm -rf "$out" && mkdir -p "$out"
cd "$root/skills"
for dir in */; do
  name="${dir%/}"
  zip -qr "$out/$name.zip" "$name" -x '*/__pycache__/*' '*.pyc' '*/.DS_Store'
  echo "built    $(basename "$out")/$name.zip"
done
