#!/usr/bin/env python3
"""Generate optimized WebP variants from the source JPG photos.

Outputs (committed to the repo, shipped in the Docker image):
  app/static/img/cities/webp/{slug}.webp         — hero, max width 960 px
  app/static/img/cities/webp/{slug}-thumb.webp   — picker card, max width 480 px

The source JPGs stay in the repo as originals but are excluded from the
Docker image via .dockerignore. Rerunnable: regenerates everything.

Usage: python scripts/optimize_images.py
"""

import sys
from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.cities import CITIES

SRC_DIR = BASE_DIR / "app" / "static" / "img" / "cities"
OUT_DIR = SRC_DIR / "webp"
HERO_WIDTH = 960
THUMB_WIDTH = 480
LQIP_WIDTH = 20  # ink-wash placeholder, embedded as base64 in the HTML
QUALITY = 80
LQIP_QUALITY = 45


def convert(source: Path, dest: Path, max_width: int,
            quality: int = QUALITY) -> None:
    with Image.open(source) as img:
        img = img.convert("RGB")
        if img.width > max_width:
            height = round(img.height * max_width / img.width)
            img = img.resize((max_width, height), Image.LANCZOS)
        img.save(dest, "WEBP", quality=quality, method=6)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    total_hero = total_thumb = 0
    for city in CITIES:
        source = SRC_DIR / f"{city['slug']}.jpg"
        if not source.is_file():
            print(f"[skip] {city['slug']}: no source jpg")
            continue
        hero = OUT_DIR / f"{city['slug']}.webp"
        thumb = OUT_DIR / f"{city['slug']}-thumb.webp"
        lqip = OUT_DIR / f"{city['slug']}-lqip.webp"
        convert(source, hero, HERO_WIDTH)
        convert(source, thumb, THUMB_WIDTH)
        convert(source, lqip, LQIP_WIDTH, LQIP_QUALITY)
        total_hero += hero.stat().st_size
        total_thumb += thumb.stat().st_size
        print(f"[ok]   {city['slug']}: héros {hero.stat().st_size // 1024} Ko · "
              f"miniature {thumb.stat().st_size // 1024} Ko · "
              f"lavis {lqip.stat().st_size} o")
    print(f"\nPicker (24 miniatures): ~{total_thumb // 1024} Ko "
          f"+ {24 * 500 // 1024} Ko de lavis embarqués")


if __name__ == "__main__":
    main()
