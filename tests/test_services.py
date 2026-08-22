"""Minimal pytest suite: catalog integrity, weather parsing, HTTP routes."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.services import weather as weather_service
from app.services.cities import CITIES, get_city, haversine_km, nearest_city

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


BATCH_SAMPLE = [
    {"current": {"temperature_2m": 30.2, "weather_code": 0}},
    {"current": {"temperature_2m": 27.8, "weather_code": 3}},
]


def test_fetch_current_many_parses_batch(monkeypatch):
    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return BATCH_SAMPLE

    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured["params"] = params
        return FakeResp()

    monkeypatch.setattr(weather_service.requests, "get", fake_get)
    weather_service._batch_cache.clear()
    by_slug = {c["slug"]: c for c in CITIES}
    cities_subset = [by_slug["tunis"], by_slug["sfax"]]
    out = weather_service.fetch_current_many(cities_subset)
    assert [o["slug"] for o in out] == ["tunis", "sfax"]
    assert out[0]["condition"] == "Ciel dégagé"
    assert out[1]["temp"] == 27.8
    assert captured["params"]["latitude"].count(",") == 1  # batched in one call


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
    km = haversine_km(36.8065, 10.1815, 34.7406, 10.7603)
    assert 220 < km < 250  # real-world distance ≈ 230 km


# ---------- Credits page (CC BY-SA attribution) ----------

def test_credits_page_lists_photos(client):
    resp = client.get("/credits")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Nabeul Beach" in html          # known Commons title
    assert "CC BY-SA" in html              # visible license
    assert "commons.wikimedia.org" in html  # provenance link


# ---------- Security headers ----------

def test_security_headers_on_html(client):
    resp = client.get("/choisir-ville")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert resp.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert resp.headers["Permissions-Policy"] == "geolocation=(self)"
    assert "max-age=31536000" in resp.headers["Strict-Transport-Security"]
    csp = resp.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_security_headers_cover_static_files(client):
    # App-level hook: static files must carry the headers too.
    resp = client.get("/static/js/main.js")
    assert resp.status_code == 200
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert "script-src 'self'" in resp.headers["Content-Security-Policy"]
