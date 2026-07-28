#!/usr/bin/env python3
"""Re-point the cache-busting `?v=` tokens at the post-PurgeCSS stylesheets.

al_folio_core stamps `style.css?v=<md5>` during the Jekyll build, but the deploy
runs PurgeCSS *after* that, rewriting the CSS in place. The pre-purge file is
produced by the gem and rarely changes, so the token stays the same while the
served bytes change every time the site's markup uses a different set of CSS
classes. Returning visitors then keep an old stylesheet forever.

That is not hypothetical: adding `row-cols-md-2` to the projects page shipped a
stylesheet containing the rule under a token browsers had already cached against
a stylesheet without it, so the page silently rendered one column wide.

Run this right after PurgeCSS and before anything copies the HTML around.
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

SITE_DIR = sys.argv[1] if len(sys.argv) > 1 else "_site"
CSS_DIR = os.path.join(SITE_DIR, "assets", "css")


def main() -> None:
    if not os.path.isdir(CSS_DIR):
        sys.exit(f"No {CSS_DIR} directory — run this after the site is built.")

    digests: dict[str, str] = {}
    for name in sorted(os.listdir(CSS_DIR)):
        if not name.endswith(".css"):
            continue
        with open(os.path.join(CSS_DIR, name), "rb") as f:
            digests[name] = hashlib.md5(f.read()).hexdigest()

    if not digests:
        sys.exit(f"No stylesheets found in {CSS_DIR}.")

    # `name.css?v=<hex>` -> the same name with the hash of what is on disk now.
    pattern = re.compile(
        r"(" + "|".join(re.escape(n) for n in digests) + r")\?v=[0-9a-f]+"
    )

    rewritten = 0
    touched = 0
    for root, _dirs, files in os.walk(SITE_DIR):
        for name in files:
            if not name.endswith((".html", ".xml")):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as f:
                original = f.read()
            updated, count = pattern.subn(
                lambda m: f"{m.group(1)}?v={digests[m.group(1)]}", original
            )
            if count and updated != original:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(updated)
                touched += 1
                rewritten += count

    for name, digest in digests.items():
        print(f"  {name} -> {digest}")
    print(f"Rewrote {rewritten} reference(s) across {touched} file(s).")


if __name__ == "__main__":
    main()
