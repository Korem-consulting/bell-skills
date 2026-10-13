#!/usr/bin/env bash
# Sanity checks for the plugin. Run from anywhere: scripts/check.sh
# - every skill dir has a SKILL.md whose frontmatter `name` equals the dir name
# - every `references/<file>` a SKILL.md points at exists inside that skill
# - both manifests parse and the plugin has a version
# - the bundled Python scripts compile
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
py="${PYTHON:-python3}"
fail=0

for dir in "$root"/skills/*/; do
  name="$(basename "$dir")"
  if [[ ! -f "$dir/SKILL.md" ]]; then echo "MISSING  $name/SKILL.md"; fail=1; continue; fi
  fm="$(sed -n '2,10p' "$dir/SKILL.md" | grep -E '^name:' | head -1 | sed -E 's/^name:[[:space:]]*//')"
  if [[ "$fm" != "$name" ]]; then echo "NAME     $name: frontmatter name is '$fm'"; fail=1; continue; fi
  # A skill is uploaded to Claude.ai as its own zip, so it may only point at
  # files inside its own directory.
  for ref in $(grep -oE '`references/[A-Za-z0-9_./-]+`' "$dir/SKILL.md" | tr -d '`' | sort -u); do
    if [[ ! -f "$dir/$ref" ]]; then echo "MISSING  $name/$ref"; fail=1; fi
  done
  if grep -q '\.\./' "$dir/SKILL.md"; then echo "ESCAPE   $name/SKILL.md points outside its own directory"; fail=1; fi
  echo "ok       $name"
done

"$py" - "$root" <<'PY' || fail=1
import json, sys, pathlib
root = pathlib.Path(sys.argv[1])
plugin = json.loads((root / ".claude-plugin/plugin.json").read_text())
json.loads((root / ".claude-plugin/marketplace.json").read_text())
assert plugin.get("version"), "plugin.json has no version"
print(f"ok       manifests (v{plugin['version']})")
PY

shopt -s nullglob
scripts=("$root"/skills/*/scripts/*.py)
if (( ${#scripts[@]} )); then "$py" -m py_compile "${scripts[@]}" && echo "ok       scripts compile"; fi

exit $fail
