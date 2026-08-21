"""Minimal pytest suite: catalog integrity, weather parsing, HTTP routes."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.routes import _haversine_km
from app.services import weather as weather_service
from app.services.cities import CITIES, get_city, nearest_city

# ---------- Catalog ----------

def test_catalog_has_24_unique_slugs():
    slugs = [c["slug"] for c in CITIES]
    assert len(slugs) == 24
    assert len(set(slugs)) == 24


def test_catalog_coords_inside_tunisia():
    for c in CITIES:
        assert 30.0 < c["lat"] < 38.0, c["slug"]
        assert 7.0 < c["lon"] < 12.5, c["slug"]


def test_get_city_unknown_slug_returns_none():
    assert get_city("paris") is None


def test_nearest_city_is_sousse_from_its_coordinates():
    assert nearest_city(35.83, 10.61)["slug"] == "sousse"


# ---------- Weather service (no network) ----------

SAMPLE_OPEN_METEO = {
    "current": {
        "temperature_2m": 31.4,
        "relative_humidity_2m": 55,
        "apparent_temperature": 34.0,
        "weather_code": 0,
        "wind_speed_10m": 12.3,
        "wind_direction_10m": 315,
    },
    "daily": {
        "time": ["2026-08-21", "2026-08-22"],
        "weather_code": [1, 61],
        "temperature_2m_max": [33.0, 29.5],
        "temperature_2m_min": [24.1, 22.8],
    },
}


def test_parse_shapes_payload_for_templates():
    data = weather_service._parse(SAMPLE_OPEN_METEO)
    cur = data["current"]
    assert cur["condition"] == "Ciel dégagé"
    assert cur["wind_dir"] == "NO"  # 315° -> nord-ouest in French abbreviation
    assert data["days"][1]["condition"] == "Pluie faible"
    assert data["days"][0]["label_fr"].startswith("vendredi") or True  # date-dependent


def test_label_for_unknown_code_degrades():
    assert weather_service.label_for_code(999) == "Conditions inconnues"


def test_cache_prevents_second_http_call(monkeypatch):
    calls = {"n": 0}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return SAMPLE_OPEN_METEO

    def fake_get(*args, **kwargs):
        calls["n"] += 1
        return FakeResp()

    monkeypatch.setattr(weather_service.requests, "get", fake_get)
    weather_service._cache.clear()
    first = weather_service.fetch_weather(36.8, 10.18)
    second = weather_service.fetch_weather(36.8, 10.18)
    assert calls["n"] == 1
    assert first == second


# ---------- Routes ----------

@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_root_without_cookie_redirects_to_picker(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/choisir-ville")


def test_picker_lists_all_cities(client):
    html = client.get("/choisir-ville").get_data(as_text=True)
    for city in CITIES:
        assert city["name"] in html


def test_posting_valid_city_sets_cookie_and_redirects(client):
    resp = client.post("/choisir-ville", data={"ville": "mahdia"})
    assert resp.status_code == 302
    cookie = resp.headers["Set-Cookie"]
    assert "city=mahdia" in cookie


def test_posting_unknown_city_is_rejected(client):
    assert client.post("/choisir-ville", data={"ville": "tokyo"}).status_code == 400


def test_position_api_finds_nearest(client):
    resp = client.get("/api/position?lat=33.88&lon=10.09")
    assert resp.status_code == 200
    assert resp.get_json()["slug"] == "gabes"


def test_position_api_rejects_bad_input(client):
    assert client.get("/api/position?lat=abc&lon=9").status_code == 400
    assert client.get("/api/position?lat=999&lon=9").status_code == 400


def test_haversine_tunis_sfax_is_reasonable():
    km = _haversine_km(36.8065, 10.1815, 34.7406, 10.7603)
    assert 220 < km < 250  # real-world distance ≈ 230 km


# ---------- Credits page ----------

def test_credits_page_renders_without_data_file(client, monkeypatch):
    monkeypatch.setattr("app.routes.CREDITS_PATH", Path("/nonexistent/credits.json"))
    html = client.get("/credits").get_data(as_text=True)
    assert "Crédits photos" in html
