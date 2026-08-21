"""HTTP routes — the whole app is four endpoints, SSR-first."""

import json
import math

from flask import Blueprint, abort, redirect, render_template, request

from . import BASE_DIR
from .services import cities as city_service
from .services import weather as weather_service

bp = Blueprint("main", __name__)

CREDITS_PATH = BASE_DIR / "data" / "image_credits.json"
IMAGES_DIR = BASE_DIR / "app" / "static" / "img" / "cities"
COOKIE_MAX_AGE = 365 * 24 * 3600


def current_city_or_none() -> dict | None:
    return city_service.get_city(request.cookies.get("city", ""))


def image_exists(city: dict) -> bool:
    return bool(city["image"]) and (IMAGES_DIR / city["image"]).is_file()


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

    return render_template(
        "index.html",
        city=city,
        has_photo=image_exists(city),
        weather=data,
        error=error_state,
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


@bp.get("/credits")
def credits():
    entries = []
    by_slug = {}
    if CREDITS_PATH.is_file():
        with open(CREDITS_PATH, encoding="utf-8") as fh:
            by_slug = json.load(fh)
    for city in city_service.CITIES:
        info = by_slug.get(city["slug"])
        if not info or not image_exists(city):
            continue
        entries.append({"city": city, **info})
    return render_template("credits.html", entries=entries)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2)
    return 6371.0 * 2 * math.asin(math.sqrt(a))
