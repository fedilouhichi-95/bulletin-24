"""Open-Meteo client, response parsing and simple in-memory cache.

The only module allowed to talk to the external weather API.
Always mock `fetch_weather` (or `requests.get`) in tests.
"""

import os
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

    Returns a plain dict ready for templates. Raises on network/HTTP errors —
    callers must handle failures and show an honest error state.
    """
    key = (round(lat, 4), round(lon, 4))
    now = time.monotonic()
    cached = _cache.get(key)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                   "weather_code,wind_speed_10m,wind_direction_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "timezone": TIMEZONE,
        "forecast_days": 5,
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    payload = _parse(resp.json())

    _cache[key] = (now, payload)
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
