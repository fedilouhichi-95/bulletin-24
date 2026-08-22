# AGENTS — conventions du projet

## Language rules

- Code, identifiers, comments, commit messages, docs: **English**
- UI strings rendered to users (templates): **French**

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate   # setup
pip install -r requirements.txt                      # deps
python run.py                                        # dev server (http://localhost:5000)
pytest                                               # tests
ruff check .                                         # lint
docker build -t almanach-meteo . && docker run -p 8000:8000 almanach-meteo
```

## Conventions

- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:` — lowercase, imperative.
- Flask app factory pattern (`create_app` in `app/__init__.py`); blueprints not needed at this size.
- City data lives ONLY in `app/services/cities.py` (slug, French name, lat/lon, riso accent).
- Weather codes mapped ONLY in `app/services/weather.py` (WMO code → French label).
- Server-side rendering first; JS only for geolocation + minor niceties.
- CSS tokens of the Lo-Fi anchor live in `app/static/css/base.css`; per-city accents in `themes.css`.
- Images: downloaded by `scripts/fetch_images.py` into `app/static/img/cities/`, then optimized to WebP by `scripts/optimize_images.py`. Credits recorded in `data/image_credits.json` (kept out of the UI by owner decision). Never hotlink.

## Interdictions

- No new dependency without asking first.
- No secrets in prompts, files or git history (`.env` is gitignored; `.env.example` documents keys).
- No manual edits inside `data/image_credits.json` (regenerate with the script).
- No new city added anywhere else than `cities.py`.
- No fabricated weather values or placeholder demo data in templates.

## Sensitive areas

- `services/weather.py`: external HTTP call — always mock in tests; cache must stay thread-safe-simple (dict + timestamp under GIL is fine at this scale).
- `scripts/fetch_images.py`: network + writes into `static/img/cities/`; rerunnable safely (idempotent-ish: skips existing files unless `--force`).
