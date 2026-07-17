#!/usr/bin/env python3
"""Regenerate _data/music.yml from NetEase Cloud Music (artist + radio).

Mirrors the pattern of scripts/update_publications.py / bin/update_scholar_citations.py:
fetch public data, write a _data/*.yml file, let the workflow commit it only when
it actually changed. Uses only NetEase's *public* GET endpoints (no login/cookie),
so it can run unattended in CI. The live site build is separate — if a run fails,
the last good _data/music.yml stays committed and the page never breaks.

Sources (override via env if they ever change):
  MUSIC_ARTIST_ID  the artist page (163cn.tv/... -> music.163.com/artist?id=<id>)
  MUSIC_RADIO_ID   the dj radio / podcast (music.163.com/#/djradio?id=<id>)
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ARTIST_ID = os.environ.get("MUSIC_ARTIST_ID", "32272234")
RADIO_ID = os.environ.get("MUSIC_RADIO_ID", "341843071")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "_data", "music.yml")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Referer": "https://music.163.com/",
    "Cookie": "NMTID=1",
}


def _get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    code = data.get("code")
    if code != 200:
        raise RuntimeError(f"NetEase returned code={code} for {url}")
    return data


def _sized(pic):
    if not pic:
        return ""
    # NetEase serves covers from a random p1/p2/p3 CDN host each request; pin it
    # to p1 so re-runs are deterministic and don't churn _data/music.yml.
    pic = re.sub(r"^https?://p\d\.music\.126\.net", "https://p1.music.126.net", pic)
    return pic + "?param=512y512"  # ask the CDN for a sensible size


def _date(ms):
    """Format a NetEase unix-ms timestamp as YYYY-MM-DD in Beijing time."""
    if not ms or ms <= 0:
        return ""
    return time.strftime("%Y-%m-%d", time.gmtime(int(ms) / 1000 + 8 * 3600))


def _by_time_desc(entries):
    """Sort newest first, then drop the private _ts sort key."""
    entries.sort(key=lambda e: e.get("_ts") or 0, reverse=True)
    for e in entries:
        e.pop("_ts", None)
    return entries


def fetch_songs(artist_id):
    """Return the artist's songs as [{title, url, cover, subtitle}], newest first."""
    data = _get(f"https://music.163.com/api/artist/{artist_id}")
    songs = data.get("hotSongs") or []
    covers = fetch_song_covers([s["id"] for s in songs])
    out = []
    for s in songs:
        meta = covers.get(s["id"], {})
        ts = meta.get("ts") or 0
        out.append(
            {
                "title": s["name"],
                "url": f"https://music.163.com/song?id={s['id']}",
                "cover": _sized(meta.get("cover", "")),
                "subtitle": _date(ts),
                "_ts": ts,
            }
        )
    return _by_time_desc(out)


def fetch_song_covers(song_ids):
    """Map song id -> {cover, ts} via the song detail endpoint."""
    if not song_ids:
        return {}
    ids = urllib.parse.quote(json.dumps(song_ids))
    data = _get(f"https://music.163.com/api/song/detail?ids={ids}")
    out = {}
    for s in data.get("songs") or []:
        album = s.get("album") or s.get("al") or {}
        out[s["id"]] = {
            "cover": album.get("picUrl") or "",
            "ts": s.get("publishTime") or album.get("publishTime") or 0,
        }
    return out


def fetch_radio(radio_id):
    """Return {name, url, episodes:[...]} for a dj radio, episodes newest first."""
    detail = _get(f"https://music.163.com/api/djradio/get?id={radio_id}")
    info = detail.get("djRadio") or {}
    progs = _get(
        f"https://music.163.com/api/dj/program/byradio"
        f"?radioId={radio_id}&limit=200&asc=false"
    ).get("programs") or []
    episodes = []
    for p in progs:
        cover = p.get("coverUrl") or ((p.get("mainSong") or {}).get("album") or {}).get("picUrl") or ""
        ts = p.get("createTime") or 0
        episodes.append(
            {
                "title": p["name"],
                "url": f"https://music.163.com/program?id={p['id']}",
                "cover": _sized(cover),
                "subtitle": _date(ts),
                "_ts": ts,
            }
        )
    return {
        "name": info.get("name") or "Radio",
        "url": f"https://music.163.com/djradio?id={radio_id}",
        "episodes": _by_time_desc(episodes),
    }


def _yaml_entry(e, indent):
    pad = " " * indent
    lines = [
        f"{pad}- title: {json.dumps(e['title'], ensure_ascii=False)}",
        f"{pad}  url: {json.dumps(e['url'], ensure_ascii=False)}",
        f"{pad}  cover: {json.dumps(e['cover'], ensure_ascii=False)}",
    ]
    if e.get("subtitle"):
        lines.append(f"{pad}  subtitle: {json.dumps(e['subtitle'], ensure_ascii=False)}")
    return lines


def dump_yaml(artist_url, songs, radio):
    # JSON strings are valid YAML scalars, so json.dumps handles all escaping
    # (Chinese titles, quotes, colons) safely without a yaml dependency.
    lines = [
        "# Auto-generated by scripts/update_music.py from NetEase (artist + radio).",
        "# Do not edit by hand — the update-music workflow overwrites this file.",
        "",
        f"artist_url: {json.dumps(artist_url, ensure_ascii=False)}",
        "",
        "songs:",
    ]
    for s in songs:
        lines += _yaml_entry(s, 0)
    lines += [
        "",
        "radio:",
        f"  name: {json.dumps(radio['name'], ensure_ascii=False)}",
        f"  url: {json.dumps(radio['url'], ensure_ascii=False)}",
        "  episodes:",
    ]
    for e in radio["episodes"]:
        lines += _yaml_entry(e, 2)
    return "\n".join(lines).rstrip() + "\n"


def main():
    try:
        songs = fetch_songs(ARTIST_ID)
        radio = fetch_radio(RADIO_ID)
    except Exception as exc:  # noqa: BLE001 — leave last-good file in place on failure
        print(f"❌ Failed to fetch music data: {exc}", file=sys.stderr)
        return 1
    if not songs and not radio["episodes"]:
        print("❌ Nothing returned; leaving _data/music.yml untouched.", file=sys.stderr)
        return 1
    artist_url = f"https://music.163.com/artist?id={ARTIST_ID}"
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(dump_yaml(artist_url, songs, radio))
    print(f"✅ Wrote {len(songs)} song(s) + {len(radio['episodes'])} radio episode(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
