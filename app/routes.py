"""HTTP routes — SSR-first, one blueprint, four endpoints."""

import math
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, redirect, render_template, request

from . import BASE_DIR
from .services import cities as city_service
from .services import weather as weather_service

bp = Blueprint("main", __name__)

IMAGES_DIR = BASE_DIR / "app" / "static" / "img" / "cities"
COOKIE_MAX_AGE = 365 * 24 * 3600
TZ_TUNIS = ZoneInfo("Africa/Tunis")

BRAND = {
    "name": "Bulletin 24",
    "tagline": "La météo imprimée des villes de Tunisie",
}


def image_exists(city: dict) -> bool:
    return bool(city["image"]) and (IMAGES_DIR / city["image"]).is_file()


@bp.app_context_processor
def inject_brand():
    """Brand block + real edition dateline for every page."""
    now = datetime.now(TZ_TUNIS)
    return {
        "brand": BRAND,
        "year": now.year,
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
    try:
        data = weather_service.fetch_weather(city["lat"], city["lon"])
    except Exception:  # noqa: BLE001 — any failure shows an honest error state
        error_state = (
            "La météo n'a pas pu être récupérée pour le moment. "
            "Réessaie dans quelques instants."
        )

    elsewhere = None
    if data is not None:
        others = [c for c in city_service.CITIES if c["slug"] != city["slug"]]
        try:
            elsewhere = weather_service.fetch_current_many(others)
        except Exception:  # noqa: BLE001 — the strip is optional decoration of real data
            elsewhere = None

    return render_template(
        "index.html",
        city=city,
        has_photo=image_exists(city),
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
                        samesite="Lax")
        return resp
    return render_template(
        "onboarding.html",
        cities=city_service.CITIES,
        images={c["slug"]: image_exists(c) for c in city_service.CITIES},
    )


@bp.get("/ville/<slug>")
def pick_city(slug: str):
    city = city_service.get_city(slug)
    if city is None:
        abort(404, description="Ville inconnue.")
    resp = redirect("/")
    resp.set_cookie("city", slug, max_age=COOKIE_MAX_AGE, httponly=True,
                    samesite="Lax")
    return resp


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
            _haversine_km(lat, lon, nearest["lat"], nearest["lon"]), 1
        ),
    }


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2)
    return 6371.0 * 2 * math.asin(math.sqrt(a))
