#!/usr/bin/env python3
"""Stamp a version onto the CSS and JS links so browsers can't serve a stale copy.

Every reference like /assets/css/site.css becomes /assets/css/site.css?v=1a2b3c4d,
where the stamp is a hash of that file's contents. Change a file, the link changes,
and the browser fetches it again instead of reusing what it already has.

Run it after editing anything in assets/ and before pushing:

    python3 tools/version_assets.py
"""

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = list(ROOT.glob("*.html")) + list(ROOT.glob("writing/*.html")) + [ROOT / "tools" / "og.html"]
LINK = re.compile(r'(?P<attr>href|src)="(?P<path>/assets/[^"?]+\.(?:css|js))(?:\?v=[0-9a-f]+)?"')


def stamp(path):
    asset = ROOT / path.lstrip("/")
    if not asset.exists():
        return None
    return hashlib.sha256(asset.read_bytes()).hexdigest()[:8]


def main():
    changed = 0
    for page in PAGES:
        if not page.exists():
            continue
        text = page.read_text(encoding="utf-8")

        def replace(match):
            version = stamp(match.group("path"))
            if version is None:
                print(f"  missing file: {match.group('path')}", file=sys.stderr)
                return match.group(0)
            return f'{match.group("attr")}="{match.group("path")}?v={version}"'

        updated = LINK.sub(replace, text)
        if updated != text:
            page.write_text(updated, encoding="utf-8")
            changed += 1
            print(f"stamped {page.relative_to(ROOT)}")

    print("nothing to change" if not changed else f"{changed} page(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
