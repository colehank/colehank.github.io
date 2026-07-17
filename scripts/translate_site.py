#!/usr/bin/env python3
"""Post-build translator: generate a light Chinese /zh/ copy of _site.

Runs in CI AFTER `jekyll build`. Scope (intentionally small):
  - every page's <title> (browser-tab name) and navbar tab labels are translated,
  - the about page (index.html) body is translated in full,
  - all OTHER page bodies are left in English.
Each /zh/ page also gets internal links rewritten under /zh/ and a 中文/EN toggle.

Fully fail-safe: any error leaves the English site untouched and exits 0.

Env: TRANSLATE_API_KEY, TRANSLATE_BASE_URL, TRANSLATE_MODEL, TRANSLATE_CACHE,
     TRANSLATE_WORKERS
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

GLOSSARY = (
    "Apply this glossary exactly: 'Guohao Zhang' -> '张国浩'; "
    "'Department of Psychology' -> '心理学部'; 'agent'/'agents' -> '智能体'; "
    "'muses' -> '灵感'. "
)

# Navbar tab labels use a fixed map (short ambiguous words translate poorly).
NAV_MAP = {
    "about": "关于",
    "publications": "出版物",
    "CV": "简历",
    "news": "新闻",
    "muses": "灵感",
}


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
    prompt = (
        "You are a professional translator for an academic personal website. "
        "Translate each item in the following JSON array from English to Simplified "
        "Chinese. Keep people's names, institution names, technical terms/acronyms "
        "(NeuroAI, fMRI, MEG, EEG, LLM, DOI, PhD, MSc, BSc), URLs, emails, code and "
        "numbers unchanged. Preserve leading/trailing spaces and punctuation. " + GLOSSARY
        + "Return ONLY a JSON array of the same length and order, no prose.\n\n"
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
        raise ValueError("bad batch response length")
    return [str(x) for x in out]


def translate_all(strings, cache):
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
        return {s: s for s in chunk}

    if chunks:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for res in ex.map(do, chunks):
                cache.update(res)
    return cache


def _text_nodes(scope, Comment):
    """Translatable text nodes within a scope element/soup."""
    out = []
    for node in scope.find_all(string=True):
        if isinstance(node, Comment):
            continue
        if node.parent and node.parent.name in SKIP_TAGS:
            continue
        if node.parent and node.parent.get("translate") == "no":
            continue
        if node.parent and "MathJax" in " ".join(node.parent.get("class", [])):
            continue
        if str(node).strip() and not str(node).strip().isdigit():
            out.append(node)
    return out


def target_nodes(soup, is_about):
    """Nodes to API-translate: <title>, and (about only) the body. Nav labels
    are handled separately via NAV_MAP."""
    from bs4 import Comment
    nodes = []
    title = soup.find("title")
    if title and title.string and title.string.strip():
        nodes.append(title.string)
    if is_about:
        body = soup.find("article") or soup.find("body") or soup
        nodes += _text_nodes(body, Comment)
    # de-dupe by object identity, preserve order
    seen, uniq = set(), []
    for n in nodes:
        if id(n) not in seen:
            seen.add(id(n))
            uniq.append(n)
    return uniq


def rewrite_links(soup):
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href == "/":
            a["href"] = "/zh/"
        elif (href.startswith("/") and not href.startswith("/zh/")
              and not href.startswith("/assets/")
              and not href.lower().endswith(ASSET_EXTS)):
            a["href"] = "/zh" + href


def apply_nav_map(soup):
    from bs4 import NavigableString
    ul = soup.find("ul", class_="navbar-nav")
    if not ul:
        return
    for a in ul.find_all("a", class_="nav-link"):
        for node in list(a.find_all(string=True)):
            key = str(node).strip()
            if key in NAV_MAP:
                node.replace_with(NavigableString(str(node).replace(key, NAV_MAP[key])))


def inject_toggle(soup, target_href, label):
    from bs4 import BeautifulSoup as BS
    ul = soup.find("ul", class_="navbar-nav")
    if not ul:
        return
    # idempotent: drop any pre-existing 中文/EN toggle first
    for a in ul.find_all("a", class_="nav-link"):
        if a.get_text(strip=True) in ("中文", "EN"):
            (a.find_parent("li") or a).decompose()
    ul.append(BS(f'<li class="nav-item"><a class="nav-link" href="{target_href}">{label}</a></li>', "html.parser"))


def main():
    if not API_KEY:
        log("no TRANSLATE_API_KEY set — skipping /zh generation")
        return 0
    try:
        from bs4 import BeautifulSoup, NavigableString
    except Exception as e:
        log(f"beautifulsoup not available: {e}")
        return 0

    import pathlib
    root = pathlib.Path(SITE)
    cache = load_cache()

    parsed, all_strings = [], set()
    for p in root.rglob("*.html"):
        rel = p.relative_to(root).as_posix()
        if rel.startswith("assets/") or rel.startswith("zh/") or rel == "404.html":
            continue
        html = p.read_text(encoding="utf-8", errors="ignore")
        if 'http-equiv="refresh"' in html.lower():
            continue
        is_about = rel == "index.html"
        soup = BeautifulSoup(html, "html.parser")
        nodes = target_nodes(soup, is_about)
        all_strings.update(str(n) for n in nodes)
        parsed.append((p, rel, soup, nodes))
    log(f"{len(parsed)} pages; translating titles + nav labels + the about body")

    translate_all(sorted(all_strings), cache)
    save_cache(cache)
    tr = lambda s: cache.get(s, s)

    count = 0
    for p, rel, soup, nodes in parsed:
        # English page: just add a 中文 toggle to the /zh/ copy
        en_soup = BeautifulSoup(str(soup), "html.parser")
        zh_href = "/zh/" if rel == "index.html" else "/zh/" + rel.replace("index.html", "")
        inject_toggle(en_soup, zh_href, "中文")
        p.write_text(str(en_soup), encoding="utf-8")

        # Chinese page: translate only the target nodes, keep the rest as-is
        for n in nodes:
            n.replace_with(NavigableString(tr(str(n))))
        apply_nav_map(soup)
        if soup.html:
            soup.html["lang"] = "zh-CN"
        rewrite_links(soup)
        en_href = "/" if rel == "index.html" else "/" + rel.replace("index.html", "")
        inject_toggle(soup, en_href, "EN")
        out = root / "zh" / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(str(soup), encoding="utf-8")
        count += 1
    log(f"wrote {count} Chinese pages under {SITE}/zh/")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"FAILED (site left English-only): {e}")
        sys.exit(0)
