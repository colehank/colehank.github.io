#!/usr/bin/env python3
"""Regenerate _bibliography/papers.bib from your ORCID record.

Why ORCID (not Google Scholar or an OpenAlex author id)?
  * Google Scholar has no official API and blocks automated scraping.
  * OpenAlex author ids are auto-disambiguated and, for common names, merge
    many different people together (a query by author id returned 167 papers).
ORCID is curated by you, so it lists exactly the works you have claimed — no
name collisions. This script reads the DOIs from your ORCID profile and looks
each one up in OpenAlex *by DOI* (an exact match) to build rich BibTeX entries.

To add a paper to your site: claim it on https://orcid.org (Works section).
The weekly GitHub Action will pick it up automatically.

Run locally: python scripts/update_publications.py
"""
from __future__ import annotations

import os
import re
import sys
import json
import time
import urllib.parse
import urllib.request

# -- Config -------------------------------------------------------------------
ORCID_ID = "0009-0008-5892-6961"    # Guohao Zhang
MAILTO = "guohao2045@gmail.com"      # OpenAlex "polite pool" — faster, nicer
BIB_PATH = "_bibliography/papers.bib"
N_SELECTED = 3                       # newest N papers flagged selected={true}

# Thumbnails shown to the left of a publication.
#
# By default the script fetches one automatically: it reads the publisher page's
# `og:image` (usually the paper's first figure) and downloads it. To pin a
# specific image instead, drop it in assets/img/publication_preview/ and map the
# DOI (lowercase, no https://doi.org/ prefix) to its filename below — a manual
# entry here always overrides the auto-fetched one.
PREVIEWS = {
    "10.1038/s41597-025-05174-7": "nod_meeg.png",
}
PREVIEW_DIR = "assets/img/publication_preview"
AUTO_PREVIEW = True  # set False to disable automatic og:image thumbnails
# -----------------------------------------------------------------------------

ORCID_API = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works"
OPENALEX = "https://api.openalex.org/works/doi:"
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _get_json(url: str, accept: str = "application/json") -> dict:
    req = urllib.request.Request(
        url,
        headers={"Accept": accept, "User-Agent": f"al-folio-updater ({MAILTO})"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def fetch_orcid_dois() -> list[str]:
    data = _get_json(ORCID_API)
    dois: list[str] = []
    for group in data.get("group", []):
        for eid in group.get("external-ids", {}).get("external-id", []):
            if (eid.get("external-id-type") or "").lower() == "doi":
                val = (eid.get("external-id-value") or "").strip().lower()
                val = val.replace("https://doi.org/", "").replace("http://doi.org/", "")
                if val and val not in dois:
                    dois.append(val)
    return dois


def fetch_openalex_by_doi(doi: str) -> dict | None:
    url = OPENALEX + urllib.parse.quote(doi, safe="") + f"?mailto={MAILTO}"
    try:
        return _get_json(url)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! OpenAlex lookup failed for {doi}: {exc}", file=sys.stderr)
        return None


def reconstruct_abstract(inv_index: dict | None) -> str:
    if not inv_index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inv_index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)


def to_bibtex_authors(authorships: list[dict]) -> str:
    names = []
    for a in authorships:
        disp = ((a.get("author") or {}).get("display_name") or "").strip()
        if not disp:
            continue
        parts = disp.split()
        if len(parts) == 1:
            names.append(parts[0])
        else:
            names.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
    return " and ".join(names)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("{", "").replace("}", "")).strip()


def make_key(work: dict, seen: set[str]) -> str:
    auth = (work.get("authorships") or [{}])[0]
    last = ((auth.get("author") or {}).get("display_name") or "anon").split()[-1].lower()
    last = re.sub(r"[^a-z]", "", last) or "anon"
    year = work.get("publication_year") or "0000"
    title = clean(work.get("title") or work.get("display_name") or "untitled").lower()
    first_word = re.sub(r"[^a-z0-9]", "", (title.split() or ["x"])[0]) or "x"
    base = f"{last}{year}{first_word}"
    key, n = base, 1
    while key in seen:
        n += 1
        key = f"{base}{n}"
    seen.add(key)
    return key


def venue(work: dict) -> tuple[str, str]:
    src = (work.get("primary_location") or {}).get("source") or {}
    return clean(src.get("display_name") or ""), clean(src.get("abbreviated_title") or "")


def _extract_og_image(html: str) -> str:
    for pat in (
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    ):
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def fetch_preview(work: dict, doi: str, key: str) -> str:
    """Download the publisher's og:image as a thumbnail. Returns a filename in
    PREVIEW_DIR, or "" if none could be fetched. Existing files are reused so the
    weekly run doesn't churn the repo."""
    if not AUTO_PREVIEW:
        return ""
    # Reuse an already-downloaded auto thumbnail for this paper, if present.
    if os.path.isdir(PREVIEW_DIR):
        for existing in os.listdir(PREVIEW_DIR):
            if existing.startswith(f"{key}."):
                return existing

    landing = (work.get("primary_location") or {}).get("landing_page_url") \
        or f"https://doi.org/{doi}"
    try:
        req = urllib.request.Request(landing, headers={"User-Agent": BROWSER_UA})
        with urllib.request.urlopen(req, timeout=45) as resp:
            html = resp.read(1_000_000).decode("utf-8", "ignore")
        img_url = _extract_og_image(html)
        if not img_url:
            return ""
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        ireq = urllib.request.Request(img_url, headers={"User-Agent": BROWSER_UA})
        with urllib.request.urlopen(ireq, timeout=45) as resp:
            ctype = resp.headers.get("Content-Type", "")
            data = resp.read(8_000_000)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! preview fetch failed for {doi}: {exc}", file=sys.stderr)
        return ""

    ext = ".png"
    if "jpeg" in ctype or "jpg" in ctype or img_url.lower().endswith((".jpg", ".jpeg")):
        ext = ".jpg"
    elif "webp" in ctype or img_url.lower().endswith(".webp"):
        ext = ".webp"
    if len(data) < 3000:  # too small to be a real figure (likely a spacer/logo)
        return ""

    os.makedirs(PREVIEW_DIR, exist_ok=True)
    fname = f"{key}{ext}"
    with open(os.path.join(PREVIEW_DIR, fname), "wb") as f:
        f.write(data)
    print(f"  + preview downloaded for {doi} -> {fname}")
    return fname


def format_entry(work: dict, key: str, selected: bool, preview: str = "") -> str:
    etype = "inproceedings" if work.get("type") == "proceedings-article" else "article"
    title = clean(work.get("title") or work.get("display_name") or "")
    authors = to_bibtex_authors(work.get("authorships") or [])
    year = work.get("publication_year") or ""
    name, abbr = venue(work)
    biblio = work.get("biblio") or {}
    doi = (work.get("doi") or "").replace("https://doi.org/", "")
    landing = (work.get("primary_location") or {}).get("landing_page_url") or ""
    abstract = clean(reconstruct_abstract(work.get("abstract_inverted_index")))

    lines = [f"@{etype}{{{key},"]
    if abbr:
        lines.append(f"  abbr={{{abbr}}},")
    lines.append("  bibtex_show={true},")
    lines.append(f"  title={{{title}}},")
    lines.append(f"  author={{{authors}}},")
    venue_field = "booktitle" if etype == "inproceedings" else "journal"
    if name:
        lines.append(f"  {venue_field}={{{name}}},")
    if biblio.get("volume"):
        lines.append(f"  volume={{{biblio['volume']}}},")
    if biblio.get("issue"):
        lines.append(f"  number={{{biblio['issue']}}},")
    if biblio.get("first_page"):
        pages = biblio["first_page"]
        if biblio.get("last_page") and biblio["last_page"] != biblio["first_page"]:
            pages = f"{biblio['first_page']}--{biblio['last_page']}"
        lines.append(f"  pages={{{pages}}},")
    if year:
        lines.append(f"  year={{{year}}},")
    if doi:
        lines.append(f"  doi={{{doi}}},")
    if landing:
        lines.append(f"  html={{{landing}}},")
    if abstract:
        lines.append(f"  abstract={{{abstract}}},")
    if preview:
        lines.append(f"  preview={{{preview}}},")
    if selected:
        lines.append("  selected={true},")
    lines.append("}")
    return "\n".join(lines)


def main() -> int:
    dois = fetch_orcid_dois()
    print(f"ORCID lists {len(dois)} work(s) with a DOI.")
    if not dois:
        print("No DOIs on ORCID; leaving papers.bib untouched.", file=sys.stderr)
        return 0

    works = []
    for doi in dois:
        w = fetch_openalex_by_doi(doi)
        if w and (w.get("title") or w.get("display_name")):
            works.append(w)
        time.sleep(0.2)  # be polite to the API

    if not works:
        print("No metadata resolved; leaving papers.bib untouched.", file=sys.stderr)
        return 0

    works.sort(key=lambda w: (w.get("publication_year") or 0), reverse=True)
    seen: set[str] = set()
    entries = []
    for i, w in enumerate(works):
        key = make_key(w, seen)
        doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
        preview = PREVIEWS.get(doi) or fetch_preview(w, doi, key)
        entries.append(format_entry(w, key, selected=i < N_SELECTED, preview=preview))

    out = "---\n---\n\n" + "\n\n".join(entries) + "\n"
    with open(BIB_PATH, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote {len(entries)} publication(s) to {BIB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
