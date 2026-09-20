#!/bin/bash
# Point the site at a custom domain (or back at github.io).
#
#   ./tools/set_domain.sh eoinkenny.ie      switch to the domain
#   ./tools/set_domain.sh eoink28.github.io switch back, and remove the CNAME file
#
# Run it from the repo root. It rewrites the addresses inside the pages, sitemap,
# robots.txt and security.txt, and writes the CNAME file GitHub Pages reads.
set -euo pipefail

NEW="${1:-}"
if [ -z "$NEW" ]; then
  echo "Usage: ./tools/set_domain.sh <domain>" >&2
  exit 1
fi

cd "$(dirname "$0")/.."

CURRENT=$(grep -ohE 'https://[a-z0-9.-]+/' index.html | head -1 | sed -E 's#https://([^/]+)/#\1#')
if [ "$CURRENT" = "$NEW" ]; then
  echo "Already pointing at $NEW"
  exit 0
fi

echo "Switching $CURRENT -> $NEW"
FILES=$(grep -rlF "$CURRENT" --include="*.html" --include="*.xml" --include="*.txt" . | grep -v '^./.git/')
for file in $FILES; do
  LC_ALL=C sed -i '' "s#$CURRENT#$NEW#g" "$file"
  echo "  updated $file"
done

if [ "$NEW" = "eoink28.github.io" ]; then
  rm -f CNAME
  echo "  removed CNAME"
else
  echo "$NEW" > CNAME
  echo "  wrote CNAME ($NEW)"
fi

echo
echo "Now: git add -A && git commit -m \"Point the site at $NEW\" && git push"
