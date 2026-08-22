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
QUALITY = 80


def convert(source: Path, dest: Path, max_width: int) -> None:
    with Image.open(source) as img:
        img = img.convert("RGB")
        if img.width > max_width:
            height = round(img.height * max_width / img.width)
            img = img.resize((max_width, height), Image.LANCZOS)
        img.save(dest, "WEBP", quality=QUALITY, method=6)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    total_before = total_after = 0
    for city in CITIES:
        source = SRC_DIR / f"{city['slug']}.jpg"
        if not source.is_file():
            print(f"[skip] {city['slug']}: no source jpg")
            continue
        hero = OUT_DIR / f"{city['slug']}.webp"
        thumb = OUT_DIR / f"{city['slug']}-thumb.webp"
        convert(source, hero, HERO_WIDTH)
        convert(source, thumb, THUMB_WIDTH)
        before = source.stat().st_size + 0  # original weight carried by page today
        after = hero.stat().st_size + thumb.stat().st_size
        total_before += before * 2  # hero+thumb were both served from the same jpg
        total_after += after
        print(f"[ok]   {city['slug']}: {after // 1024} Ko webp "
              f"(source {before // 1024} Ko)")
    print(f"\nPicker payload: ~{total_after // 1024} Ko webp vs "
          f"~{total_before // 1048576} Mo jpg avant")


if __name__ == "__main__":
    main()
