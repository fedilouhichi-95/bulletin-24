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
- 24 city photos downloaded from Wikimedia Commons into `app/static/img/cities/`
  with credits in `data/image_credits.json`, shown on `/credits`
  (typographic hero variant kept in code as fallback for missing images)
- Tests: 16 pytest cases (catalog, parsing, cache, routes, credits page) — green
- Lint: ruff — clean
- DevOps: Dockerfile (gunicorn), docker-compose.yml, GitHub Actions CI
  (ruff → pytest → docker build). Local gunicorn run verified; docker build
  to be verified once a Docker daemon is available (CI covers it too).

## 🔜 Next (SPEC features)

1. Onboarding polish: remember last visit, nicer thumbnails crop (feature #1 done at basic level)
2. Per-city theme refinements (feature #2): two-ink compositions, region-photo captions review
3. Current-weather extras from Open-Meteo (UV, precipitation probability) if wanted
4. Hourly forecast strip (not in v1 SPEC — ask before adding)
5. Deployment phase DONE: live on Render free tier — https://bulletin-24.onrender.com
   - `render.yaml` blueprint, Docker runtime, autoDeploy on main (CD via Render)
   - Runtime smoke test added to CI (docker run + curl) after a startup bug
     (`app:create_app()` parens broke dash) — fixed with `wsgi.py` entrypoint
   - Perf: Pillow pipeline (`scripts/optimize_images.py`) generates WebP hero
     (960 px) + thumb (480 px); picker payload ~6 Mo → ~0,9 Mo; static assets
     cached 1 year; source JPGs excluded from the image via `.dockerignore`
   - Keep-alive: external cron-job.org pings /choisir-ville every 10 min so the
     free instance never sleeps (~730 h of the 750 h monthly allowance)

## 📌 Decisions taken

- Product renamed **Bulletin 24** (was "Almanach du Ciel", then "Sama") — single
  source of truth: `BRAND` dict in `app/routes.py`, templates use `{{ brand.name }}`
- Three-dot menu (top-left, `<details>` HTML, no JS to open) hosts city change,
  geolocation and credits; "Ma position" also stays on the weather page — both
  share the same `[data-geoloc]` JS handler loaded on every page
- Footer reduced to the legal line only (© Fedi Louhichi)
- Photo captions and the /credits page were removed at owner's request, then
  **restored (2026-08-22)**: most images are CC BY-SA, which requires visible
  attribution — the `/credits` page and menu link are back, fed by
  `data/image_credits.json`.
- Masthead title links to /choisir-ville; dateline shows only the edition line

- SSR-first Flask; cookie (not localStorage) so the server renders per-city directly
- No database, no auth in v1 (see SPEC.md out-of-scope)
- Region photos used only where the capital lacks a usable free photo,
  always captioned « Région de X » and credited
- Images bundled in repo (no hotlinking); credits regenerated only by script
