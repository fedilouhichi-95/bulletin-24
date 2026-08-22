"""Open-Meteo client, response parsing and simple in-memory cache.

The only module allowed to talk to the external weather API.
Always mock `fetch_weather` (or `requests.get`) in tests.
"""

import os
import threading
import time

import requests

OPEN_METEO_URL = os.environ.get("OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast")
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_MINUTES", "30")) * 60
TIMEZONE = "Africa/Tunis"
REQUEST_TIMEOUT = 8  # seconds

# WMO weather interpretation codes -> French labels (UI language).
WMO_LABELS = {
    0: "Ciel dégagé",
    1: "Ciel majoritairement dégagé",
    2: "Partiellement nuageux",
    3: "Ciel couvert",
    45: "Brouillard",
    48: "Brouillard givrant",
    51: "Bruine légère",
    53: "Bruine modérée",
    55: "Bruine dense",
    56: "Bruine verglaçante légère",
    57: "Bruine verglaçante dense",
    61: "Pluie faible",
    63: "Pluie modérée",
    65: "Pluie forte",
    66: "Pluie verglaçante faible",
    67: "Pluie verglaçante forte",
    71: "Neige faible",
    73: "Neige modérée",
    75: "Neige forte",
    77: "Grains de neige",
    80: "Averses faibles",
    81: "Averses modérées",
    82: "Averses violentes",
    85: "Averses de neige faibles",
    86: "Averses de neige fortes",
    95: "Orage",
    96: "Orage avec grêle légère",
    99: "Orage avec grêle forte",
}

# French compass abbreviations (Ouest = O, Sud-Ouest = SO...).
_COMPASS = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]

# Locale-independent French weekday names (Monday first).
_WEEKDAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin",
              "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

# Thread-safe-enough cache at this scale: dict + timestamps under the GIL.
_cache: dict[tuple[float, float], tuple[float, dict]] = {}
_batch_cache: dict[tuple[str, ...], tuple[float, list[dict]]] = {}
_refreshing: set[tuple[float, float]] = set()


def label_for_code(code) -> str:
    """Map a WMO code to its French label; unknown codes degrade honestly."""
    return WMO_LABELS.get(int(code), "Conditions inconnues")


def compass(degrees) -> str:
    return _COMPASS[round((float(degrees) % 360) / 45) % 8]


def format_date_fr(iso_date: str) -> str:
    """'2026-08-21' -> 'vendredi 21 août'."""
    year, month, day = (int(p) for p in iso_date.split("-"))
    import datetime

    weekday = datetime.date(year, month, day).weekday()
    return f"{_WEEKDAYS_FR[weekday]} {day} {_MONTHS_FR[month - 1]}"


def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch current conditions + 5-day forecast for a point.

    Stale-While-Revalidate: an expired cache entry is served immediately
    while a daemon thread refreshes it for the next visitor. Raises only
    when there is nothing cached at all — callers must handle that case.
    """
    key = (round(lat, 4), round(lon, 4))
    now = time.monotonic()
    entry = _cache.get(key)
    if entry:
        timestamp, payload = entry
        if now - timestamp < CACHE_TTL_SECONDS:
            return payload
        if key not in _refreshing:
            _refreshing.add(key)
            threading.Thread(target=_refresh, args=(lat, lon, key),
                             daemon=True).start()
        return payload
    return _fetch_and_store(lat, lon, key)


def _refresh(lat: float, lon: float, key: tuple[float, float]) -> None:
    try:
        _fetch_and_store(lat, lon, key)
    except Exception as exc:  # noqa: BLE001 — stale data beats a broken page
        print(f"[weather] background refresh failed for {key}: {exc}",
              flush=True)
    finally:
        _refreshing.discard(key)


def _fetch_and_store(lat: float, lon: float,
                     key: tuple[float, float]) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                   "weather_code,wind_speed_10m,wind_direction_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "timezone": TIMEZONE,
        "forecast_days": 5,
    }
    resp = requests.get(OPEN_METEO_URL, params=params,
                        timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    payload = _parse(resp.json())

    _cache[key] = (time.monotonic(), payload)
    return payload


def _parse(data: dict) -> dict:
    """Shape the raw Open-Meteo JSON into template-friendly data."""
    cur = data["current"]
    daily = data["daily"]
    days = [
        {
            "iso": iso,
            "label_fr": format_date_fr(iso),
            "code": code,
            "condition": label_for_code(code),
            "tmax": tmax,
            "tmin": tmin,
        }
        for iso, code, tmax, tmin in zip(
            daily["time"],
            daily["weather_code"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            strict=True,
        )
    ]
    return {
        "current": {
            "temp": cur["temperature_2m"],
            "feels_like": cur["apparent_temperature"],
            "humidity": cur["relative_humidity_2m"],
            "code": cur["weather_code"],
            "condition": label_for_code(cur["weather_code"]),
            "wind_kmh": cur["wind_speed_10m"],
            "wind_dir": compass(cur["wind_direction_10m"]),
        },
        "days": days,
    }


def fetch_current_many(city_list: list[dict]) -> list[dict] | None:
    """Current temperature for many cities in ONE batched API call.

    Returns [{slug, name, temp, condition}, ...] in input order,
    or None on any failure — the caller degrades to hiding the strip.
    """
    slugs = tuple(c["slug"] for c in city_list)
    now = time.monotonic()
    cached = _batch_cache.get(slugs)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    params = {
        "latitude": ",".join(str(c["lat"]) for c in city_list),
        "longitude": ",".join(str(c["lon"]) for c in city_list),
        "current": "temperature_2m,weather_code",
        "timezone": TIMEZONE,
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):  # single-coordinate responses are not lists
        data = [data]

    out = [
        {
            "slug": city["slug"],
            "name": city["name"],
            "temp": item["current"]["temperature_2m"],
            "condition": label_for_code(item["current"]["weather_code"]),
        }
        for city, item in zip(city_list, data, strict=True)
    ]
    _batch_cache[slugs] = (now, out)
    return out
