#!/usr/bin/env bash
# Clones the pinned open-source analysis targets into ./targets (macOS/Linux equivalent of setup-targets.ps1).
# Some targets are intentionally OLD, VULNERABLE versions for defensive study only. Never deploy them.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$root/targets"

while read -r name url tag; do
  [ -z "$name" ] && continue
  dest="$root/targets/$name"
  if [ -d "$dest" ]; then echo "skip   $name (already present)"; continue; fi
  echo "clone  $name @ $tag"
  git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$tag" "$url" "$dest"
done <<'EOF'
tinydb          https://github.com/msiemens/tinydb.git     v4.8.0
flask           https://github.com/pallets/flask.git       3.0.3
express         https://github.com/expressjs/express.git   4.21.2
bottle          https://github.com/bottlepy/bottle.git     0.13.2
minimist-1.2.5  https://github.com/minimistjs/minimist.git v1.2.5
minimist-1.2.6  https://github.com/minimistjs/minimist.git v1.2.6
requests-2.30.0 https://github.com/psf/requests.git        v2.30.0
requests-2.31.0 https://github.com/psf/requests.git        v2.31.0
EOF

echo "Done. Targets are in $root/targets (git-ignored)."
