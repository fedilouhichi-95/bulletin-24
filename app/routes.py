"""HTTP routes — SSR-first, one blueprint, five endpoints."""

import base64
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, redirect, render_template, request

from . import BASE_DIR
from .services import cities as city_service
from .services import weather as weather_service

bp = Blueprint("main", __name__)

IMAGES_DIR = BASE_DIR / "app" / "static" / "img" / "cities"
CREDITS_FILE = BASE_DIR / "data" / "image_credits.json"
COOKIE_MAX_AGE = 365 * 24 * 3600
TZ_TUNIS = ZoneInfo("Africa/Tunis")


def _load_css_bundle() -> str:
    """Both stylesheets inlined into <head>: zero render-blocking requests."""
    css_dir = BASE_DIR / "app" / "static" / "css"
    return (css_dir / "base.css").read_text(encoding="utf-8") + "\n" + (
        css_dir / "themes.css"
    ).read_text(encoding="utf-8")


# Read once at import time; the bundle only changes on deploy.
_CSS_BUNDLE = _load_css_bundle()

BRAND = {
    "name": "Bulletin 24",
    "tagline": "La météo imprimée des villes de Tunisie",
}


def image_exists(city: dict) -> bool:
    """True when optimized WebP variants exist for the city."""
    return (IMAGES_DIR / "webp" / f"{city['slug']}.webp").is_file()


def image_paths(city: dict) -> dict:
    """Static-file paths of the optimized variants for templates."""
    return {
        "hero": f"img/cities/webp/{city['slug']}.webp",
        "thumb": f"img/cities/webp/{city['slug']}-thumb.webp",
        "lqip": _lqip_data_uri(city["slug"]),
    }


_lqip_cache: dict[str, str] = {}


def _lqip_data_uri(slug: str) -> str | None:
    """Tiny blurred ink-wash placeholder embedded straight into the HTML."""
    if slug not in _lqip_cache:
        path = IMAGES_DIR / "webp" / f"{slug}-lqip.webp"
        if not path.is_file():
            return None
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        _lqip_cache[slug] = f"data:image/webp;base64,{encoded}"
    return _lqip_cache[slug]


@bp.app_context_processor
def inject_brand():
    """Brand block, real edition dateline and inlined CSS for every page."""
    now = datetime.now(TZ_TUNIS)
    return {
        "brand": BRAND,
        "year": now.year,
        "css_bundle": _CSS_BUNDLE,
        "edition_fr": f"Édition de {now.strftime('%H:%M')} — "
                      f"{weather_service.format_date_fr(now.date().isoformat())} {now.year}",
    }


def current_city_or_none() -> dict | None:
    return city_service.get_city(request.cookies.get("city", ""))


@bp.get("/")
def index():
    city = current_city_or_none()
    if city is None:
        return redirect("/choisir-ville")

    error_state = None
    data = None
    others = [c for c in city_service.CITIES if c["slug"] != city["slug"]]

    # Both Open-Meteo calls in parallel: the strip never waits on the main fetch.
    with ThreadPoolExecutor(max_workers=2) as pool:
        main_future = pool.submit(weather_service.fetch_weather,
                                  city["lat"], city["lon"])
        strip_future = pool.submit(weather_service.fetch_current_many, others)
        try:
            data = main_future.result()
        except Exception:  # noqa: BLE001 — any failure shows an honest error state
            error_state = (
                "La météo n'a pas pu être récupérée pour le moment. "
                "Réessaie dans quelques instants."
            )
        elsewhere = None
        if data is not None:
            try:
                elsewhere = strip_future.result()
            except Exception:  # noqa: BLE001 — optional decoration of real data
                elsewhere = None

    return render_template(
        "index.html",
        city=city,
        image=image_paths(city) if image_exists(city) else None,
        weather=data,
        error=error_state,
        elsewhere=elsewhere,
    )


@bp.route("/choisir-ville", methods=["GET", "POST"])
def choisir_ville():
    if request.method == "POST":
        slug = request.form.get("ville", "")
        city = city_service.get_city(slug)
        if city is None:
            abort(400, description="Ville inconnue.")
        resp = redirect("/")
        resp.set_cookie("city", slug, max_age=COOKIE_MAX_AGE, httponly=True,
                        samesite="Lax", secure=request.is_secure)
        return resp
    return render_template(
        "onboarding.html",
        cities=city_service.CITIES,
        images={c["slug"]: image_paths(c) if image_exists(c) else None
                for c in city_service.CITIES},
    )


@bp.get("/ville/<slug>")
def pick_city(slug: str):
    city = city_service.get_city(slug)
    if city is None:
        abort(404, description="Ville inconnue.")
    resp = redirect("/")
    resp.set_cookie("city", slug, max_age=COOKIE_MAX_AGE, httponly=True,
                    samesite="Lax", secure=request.is_secure)
    return resp


@bp.get("/credits")
def credits():
    """Photo attributions — CC BY-SA requires visible credit."""
    entries: dict[str, dict] = {}
    if CREDITS_FILE.is_file():
        entries = json.loads(CREDITS_FILE.read_text(encoding="utf-8"))
    photos = []
    for slug, meta in entries.items():
        city = city_service.get_city(slug)
        photos.append({
            "city_name": city["name"] if city else slug,
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "license": meta.get("license", ""),
            "page_url": meta.get("page_url", ""),
        })
    return render_template("credits.html", photos=photos)


@bp.get("/api/position")
def api_position():
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        abort(400, description="Coordonnées invalides.")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        abort(400, description="Coordonnées hors limites.")
    nearest = city_service.nearest_city(lat, lon)
    return {
        "slug": nearest["slug"],
        "name": nearest["name"],
        "distance_km": round(
            city_service.haversine_km(lat, lon, nearest["lat"], nearest["lon"]), 1
        ),
    }
