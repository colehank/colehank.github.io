#!/usr/bin/env python3
"""Post-build translator: generate a Simplified-Chinese /zh/ copy of _site.

Runs in CI AFTER `jekyll build`. For every HTML page under _site it:
  - translates the visible text (and <title>) to Chinese via an OpenAI-compatible
    chat API (batched + cached),
  - rewrites internal page links to stay under /zh/,
  - injects a language toggle (中文 / EN) into the navbar,
  - writes the result to _site/zh/<same path>.
The English pages get the same toggle (pointing at the /zh/ copy).

Fully fail-safe: any error (missing key, API failure, parse error) leaves the
English site untouched and exits 0, so the site always deploys.

Env:
  TRANSLATE_API_KEY   OpenAI-compatible API key (required; skip if missing)
  TRANSLATE_BASE_URL  e.g. https://www.dmxapi.cn/v1
  TRANSLATE_MODEL     e.g. gpt-4o
  TRANSLATE_CACHE     path to a JSON translation cache (default .translate-cache.json)
"""

import json
import os
import sys
import time
import urllib.request

SITE = sys.argv[1] if len(sys.argv) > 1 else "_site"
API_KEY = os.environ.get("TRANSLATE_API_KEY", "")
BASE_URL = os.environ.get("TRANSLATE_BASE_URL", "https://www.dmxapi.cn/v1").rstrip("/")
MODEL = os.environ.get("TRANSLATE_MODEL", "gpt-4o")
CACHE_PATH = os.environ.get("TRANSLATE_CACHE", ".translate-cache.json")

SKIP_TAGS = {"script", "style", "code", "pre", "kbd", "samp", "tt", "noscript", "svg"}
ASSET_EXTS = (".pdf", ".xml", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
              ".json", ".ico", ".css", ".js", ".woff", ".woff2", ".ttf", ".zip")


def log(m):
    print(f"[translate] {m}", flush=True)


def load_cache():
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception as e:
        log(f"could not write cache: {e}")


def translate_batch(texts):
    """Translate a list of strings to Chinese; returns a same-length list."""
    prompt = (
        "You are a professional translator for an academic personal website. "
        "Translate each item in the following JSON array from English to Simplified "
        "Chinese. Keep proper nouns, people's names, institution names, technical "
        "terms/acronyms (e.g. NeuroAI, fMRI, MEG, EEG, LLM, DOI, PhD, MSc, BSc), URLs, "
        "emails, code and numbers unchanged. Preserve leading/trailing spaces and "
        "punctuation. Return ONLY a JSON array of the same length, same order, no prose.\n\n"
        + json.dumps(texts, ensure_ascii=False)
    )
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("```")[1].lstrip("json").strip()
    out = json.loads(content)
    if not isinstance(out, list) or len(out) != len(texts):
        raise ValueError(f"bad batch response ({len(out) if isinstance(out, list) else '?'} != {len(texts)})")
    return [str(x) for x in out]


def translate_all(strings, cache):
    """Translate unique strings concurrently (I/O-bound API calls)."""
    from concurrent.futures import ThreadPoolExecutor

    todo = [s for s in strings if s not in cache]
    log(f"{len(strings)} unique strings, {len(todo)} to translate")
    CHUNK = 25
    WORKERS = int(os.environ.get("TRANSLATE_WORKERS", "8"))
    chunks = [todo[i:i + CHUNK] for i in range(0, len(todo), CHUNK)]

    def do(chunk):
        for attempt in range(3):
            try:
                return dict(zip(chunk, translate_batch(chunk)))
            except Exception as e:
                log(f"chunk attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(2)
        return {s: s for s in chunk}  # give up -> keep English

    if chunks:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for res in ex.map(do, chunks):  # merged in the main thread
                cache.update(res)
    return cache


def translatable_strings(soup):
    from bs4 import NavigableString, Comment
    out = []
    for node in soup.find_all(string=True):
        if isinstance(node, Comment):
            continue
        parent = node.parent.name if node.parent else ""
        if parent in SKIP_TAGS:
            continue
        if node.parent and node.parent.get("translate") == "no":
            continue
        if node.parent and "MathJax" in " ".join(node.parent.get("class", [])):
            continue
        text = str(node)
        if text.strip() and not text.strip().isdigit():
            out.append(text)
    return out


def rewrite_links(soup, to_zh):
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if to_zh:
            if (href.startswith("/") and not href.startswith("/zh/")
                    and not href.startswith("/assets/")
                    and not href.lower().endswith(ASSET_EXTS)):
                a["href"] = "/zh" + ("" if href == "/" else href) if href != "/" else "/zh/"
    # normalise "/" -> "/zh/"
    for a in soup.find_all("a", href=True):
        if a["href"] == "/zh":
            a["href"] = "/zh/"


def inject_toggle(soup, target_href, label):
    ul = soup.find("ul", class_="navbar-nav")
    if not ul:
        return
    from bs4 import BeautifulSoup as BS
    li = BS(
        f'<li class="nav-item"><a class="nav-link" href="{target_href}">{label}</a></li>',
        "html.parser",
    )
    ul.append(li)


def main():
    if not API_KEY:
        log("no TRANSLATE_API_KEY set — skipping /zh generation")
        return 0
    try:
        from bs4 import BeautifulSoup
    except Exception as e:
        log(f"beautifulsoup not available: {e}")
        return 0

    import pathlib
    root = pathlib.Path(SITE)
    pages = []
    for p in root.rglob("*.html"):
        rel = p.relative_to(root).as_posix()
        if rel.startswith("assets/") or rel.startswith("zh/") or rel == "404.html":
            continue
        html = p.read_text(encoding="utf-8", errors="ignore")
        if 'http-equiv="refresh"' in html.lower():
            continue  # redirect stub
        pages.append((p, rel, html))
    log(f"{len(pages)} pages to translate")

    cache = load_cache()
    # gather all strings first (one big translate pass -> better batching/caching)
    all_strings = set()
    parsed = []
    for p, rel, html in pages:
        soup = BeautifulSoup(html, "html.parser")
        strings = translatable_strings(soup)
        title = soup.find("title")
        if title and title.string and title.string.strip():
            strings.append(str(title.string))
        all_strings.update(strings)
        parsed.append((p, rel, soup))
    translate_all(sorted(all_strings), cache)
    save_cache(cache)

    def tr(s):
        return cache.get(s, s)

    from bs4 import NavigableString, Comment
    count = 0
    for p, rel, soup in parsed:
        # english page: add a "中文" toggle pointing at the zh copy
        en_soup = BeautifulSoup(str(soup), "html.parser")
        zh_path = "/zh/" if rel == "index.html" else "/zh/" + rel.replace("index.html", "")
        inject_toggle(en_soup, zh_path, "中文")
        p.write_text(str(en_soup), encoding="utf-8")

        # chinese page
        for node in soup.find_all(string=True):
            if isinstance(node, Comment):
                continue
            parent = node.parent.name if node.parent else ""
            if parent in SKIP_TAGS:
                continue
            if node.parent and node.parent.get("translate") == "no":
                continue
            if node.parent and "MathJax" in " ".join(node.parent.get("class", [])):
                continue
            t = str(node)
            if t.strip() and not t.strip().isdigit():
                node.replace_with(NavigableString(tr(t)))
        title = soup.find("title")
        if title and title.string and title.string.strip():
            title.string.replace_with(tr(str(title.string)))
        soup.html["lang"] = "zh-CN" if soup.html else None
        rewrite_links(soup, to_zh=True)
        en_path = "/" if rel == "index.html" else "/" + rel.replace("index.html", "")
        inject_toggle(soup, en_path, "EN")

        out = root / "zh" / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(str(soup), encoding="utf-8")
        count += 1
    log(f"wrote {count} Chinese pages under {SITE}/zh/")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # never break the deploy
        log(f"FAILED (site left English-only): {e}")
        sys.exit(0)
