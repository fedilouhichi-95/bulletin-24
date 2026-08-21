#!/usr/bin/env python3
"""Download one free-licensed photo per city from Wikimedia Commons.

Strategy per city:
  1. If `seed` (exact verified filename) is set, fetch that file.
  2. Otherwise search Commons for `query` and take the first bitmap hit.
Metadata (title, author, license, page URL) is written to data/image_credits.json,
which the /credits page reads. Rerunnable: existing files are skipped unless --force.

Usage: python scripts/fetch_images.py [--force]
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.cities import CITIES

API = "https://commons.wikimedia.org/w/api.php"
OUT_DIR = BASE_DIR / "app" / "static" / "img" / "cities"
CREDITS_FILE = BASE_DIR / "data" / "image_credits.json"
THUMB_WIDTH = 1200
UA = {"User-Agent": "almanach-meteo-scaffold/1.0 (educational project)"}
PAUSE_BETWEEN_CITIES = 3      # seconds — be polite to Commons
RETRY_DELAYS = [15, 30, 60]   # backoff schedule on HTTP 429


def get_with_backoff(url: str, timeout: int = 30, **kwargs) -> requests.Response:
    for attempt, delay in enumerate([*RETRY_DELAYS, None]):
        resp = requests.get(url, headers=UA, timeout=timeout, **kwargs)
        if resp.status_code != 429 or delay is None:
            return resp
        print(f"[wait] 429 rate-limited, sleeping {delay}s...")
        time.sleep(delay)
    return resp


def api_get(params: dict) -> dict:
    resp = get_with_backoff(API, params={**params, "format": "json"})
    resp.raise_for_status()
    return resp.json()


def resolve_file(city: dict) -> str | None:
    """Return the chosen Commons filename for a city."""
    if city["seed"]:
        return city["seed"]
    if not city["query"]:
        return None
    data = api_get({
        "action": "query",
        "list": "search",
        "srsearch": city["query"],
        "srnamespace": 6,  # File namespace
        "srlimit": 5,
    })
    hits = data.get("query", {}).get("search", [])
    for hit in hits:
        title = hit["title"]  # "File:Foo.jpg"
        if re.search(r"\.(jpe?g|png|webp)$", title, re.IGNORECASE):
            return title.removeprefix("File:")
    return None


def download(city: dict, filename: str, force: bool) -> bool:
    dest = OUT_DIR / city["image"]
    if dest.is_file() and not force:
        print(f"[skip] {city['slug']} ({dest.name} exists)")
        return True
    data = api_get({
        "action": "query",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": THUMB_WIDTH,
    })
    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return False
    info = next(iter(pages.values())).get("imageinfo", [{}])[0]
    url = info.get("thumburl") or info.get("url")
    if not url:
        return False

    meta = info.get("extmetadata", {})

    def clean(value_key: str) -> str:
        raw = meta.get(value_key, {}).get("value", "")
        return re.sub(r"<[^>]+>", "", raw).strip()

    img = get_with_backoff(url)
    img.raise_for_status()
    dest.write_bytes(img.content)

    credits[city["slug"]] = {
        "title": clean("ObjectName") or filename,
        "author": clean("Artist") or "Auteur inconnu",
        "license": clean("LicenseShortName") or "Voir la source",
        "page_url": f"https://commons.wikimedia.org/wiki/File:{filename.replace(' ', '_')}",
        "file": filename,
    }
    print(f"[ok]   {city['slug']} <- {filename}")
    return True


credits: dict[str, dict] = {}
if CREDITS_FILE.is_file():
    credits = json.loads(CREDITS_FILE.read_text(encoding="utf-8"))

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--force", action="store_true", help="redownload existing files")
args = parser.parse_args()

OUT_DIR.mkdir(parents=True, exist_ok=True)
CREDITS_FILE.parent.mkdir(parents=True, exist_ok=True)

failures: list[str] = []
for city in CITIES:
    if not city["image"]:
        continue  # typographic variant (e.g. Ariana)
    try:
        filename = resolve_file(city)
        if not filename or not download(city, filename, args.force):
            failures.append(city["slug"])
            print(f"[FAIL] {city['slug']}: no usable file found")
    except Exception as exc:  # noqa: BLE001 — report and continue with other cities
        failures.append(city["slug"])
        print(f"[FAIL] {city['slug']}: {exc}")
    time.sleep(PAUSE_BETWEEN_CITIES)

CREDITS_FILE.write_text(
    json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"\n{len(credits)} credit(s) written to {CREDITS_FILE.relative_to(BASE_DIR)}")
if failures:
    print(f"Failed cities: {', '.join(failures)}")
    sys.exit(1)
