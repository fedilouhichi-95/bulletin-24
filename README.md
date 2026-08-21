# Bulletin 24

Weather web app for the 24 governorate capitals of Tunisia. Each city renders as a
screen-printed almanac page (Lo-Fi / risograph aesthetic) with its own free-licensed
photo and riso ink accent. Weather data by [Open-Meteo](https://open-meteo.com)
(free, no API key).

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py            # http://localhost:5000
```

## Commands

| Command | What it does |
|---|---|
| `python run.py` | dev server with reload |
| `pytest` | test suite |
| `ruff check .` | lint |
| `docker build -t almanach-meteo . && docker run -p 8000:8000 almanach-meteo` | containerized run |
| `python scripts/fetch_images.py` | (re)download city photos from Wikimedia Commons |

## Layout

- `app/` — Flask app: `routes.py`, `services/cities.py` (24 cities), `services/weather.py` (Open-Meteo + cache)
- `app/templates/` — server-rendered pages (French UI), `app/static/` — CSS tokens, geoloc JS, city photos
- `data/image_credits.json` — photo attributions, shown on `/credits` (regenerate via script, never hand-edit)
- `tests/` — pytest suite; `.github/workflows/ci.yml` — lint → tests → docker build

See `SPEC.md` for scope and `AGENTS.md` for project conventions.
