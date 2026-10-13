#!/usr/bin/env bash
# Fail when the shipped skills or manifests changed since BASE but the plugin
# version was not raised. Claude Code only offers an update when `version`
# changes, so an unbumped change never reaches anyone who installed it.
#
#   scripts/check-version.sh origin/main [extra git pathspecs...]
set -euo pipefail
base="${1:?usage: check-version.sh <base-ref>}"
root="$(cd "$(dirname "$0")/.." && pwd)"
top="$(git -C "$root" rev-parse --show-toplevel)"
prefix="${root#"$top"}"; prefix="${prefix#/}"; prefix="${prefix:+$prefix/}"
manifest="${prefix}.claude-plugin/plugin.json"

changed="$(git -C "$top" diff --name-only "$base"...HEAD -- \
  "${prefix}skills" "${prefix}.claude-plugin" "${@:2}")"
if [[ -z "$changed" ]]; then echo "ok       no shipped files changed"; exit 0; fi

ver() { git -C "$top" show "$1:$manifest" 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["version"])' 2>/dev/null || echo 0.0.0; }
old="$(ver "$(git -C "$top" merge-base "$base" HEAD)")"
new="$(ver HEAD)"
if [[ "$old" != "$new" && "$(printf '%s\n%s\n' "$old" "$new" | sort -V | tail -1)" == "$new" ]]; then
  echo "ok       version $old -> $new"
else
  echo "VERSION  shipped files changed but plugin.json version is $new (base $old) — raise it:"
  echo "$changed" | sed 's/^/           /'
  exit 1
fi
