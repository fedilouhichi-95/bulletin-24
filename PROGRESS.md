# PROGRESS

## ✅ Done (scaffold)

- Flask app factory (`app/__init__.py`), routes, Jinja templates (French UI)
- Catalog of the 24 Tunisian governorate capitals (`app/services/cities.py`)
  with coordinates, riso accents, verified Commons seeds/queries
- Open-Meteo client: current weather + 5-day forecast, WMO → French labels,
  French dates, compass directions, in-memory cache (30 min TTL)
- City picker onboarding via `city` cookie; unknown slug rejected
- Geolocation button (`main.js`) → `/api/position` nearest-city haversine
- Lo-Fi "Almanach tunisien" design: paper-yellow surface, system font mix,
  halftone photo screens, riso misregistration, rotated elements, per-city accent
- 23 city photos downloaded from Wikimedia Commons into `app/static/img/cities/`
  with credits in `data/image_credits.json`, shown on `/credits`
  (Ariana = typographic variant by design)
- Tests: 15 pytest cases (catalog, parsing, cache, routes, credits) — green
- Lint: ruff — clean
- DevOps: Dockerfile (gunicorn), docker-compose.yml, GitHub Actions CI
  (ruff → pytest → docker build). Local gunicorn run verified; docker build
  to be verified once a Docker daemon is available (CI covers it too).

## 🔜 Next (SPEC features)

1. Onboarding polish: remember last visit, nicer thumbnails crop (feature #1 done at basic level)
2. Per-city theme refinements (feature #2): two-ink compositions, region-photo captions review
3. Current-weather extras from Open-Meteo (UV, precipitation probability) if wanted
4. Hourly forecast strip (not in v1 SPEC — ask before adding)
5. Deployment phase: provision VPS, install Docker, add CD job (SSH deploy) behind secrets

## 📌 Decisions taken

- SSR-first Flask; cookie (not localStorage) so the server renders per-city directly
- No database, no auth in v1 (see SPEC.md out-of-scope)
- Region photos used only where the capital lacks a usable free photo,
  always captioned « Région de X » and credited
- Images bundled in repo (no hotlinking); credits regenerated only by script
