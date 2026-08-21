"""Single source of truth for Tunisian cities (24 governorate capitals).

Each entry:
  slug     — URL/cookie-safe identifier
  name     — French display name
  lat/lon  — coordinates used directly with Open-Meteo (no geocoding needed)
  accent   — riso-ink accent color for the city page (themes are generated from this)
  image    — expected filename in static/img/cities/ or None (typographic variant)
  query    — Wikimedia Commons search terms used by scripts/fetch_images.py
  seed     — exact Commons filename when one was verified, else None
  note     — honest caption hint when the photo depicts a region landmark, not the capital itself
"""

CITIES = [
    # --- North ---
    {"slug": "tunis", "name": "Tunis", "lat": 36.8065, "lon": 10.1815,
     "accent": "#0078BF", "image": "tunis.jpg", "seed": None,
     "query": "Tunis medina street Tunisia", "note": None},
    {"slug": "ariana", "name": "Ariana", "lat": 36.8625, "lon": 10.1956,
     "accent": "#FF48B0", "image": None, "seed": None,
     "query": "", "note": None},
    {"slug": "ben-arous", "name": "Ben Arous", "lat": 36.7533, "lon": 10.2283,
     "accent": "#FF6C2F", "image": "ben-arous.jpg",
     "seed": "Hammam-Lif Palais Beylical v001.jpg",
     "query": "Hammam Lif palace Tunisia", "note": "Région de Ben Arous"},
    {"slug": "manouba", "name": "La Manouba", "lat": 36.8080, "lon": 10.0972,
     "accent": "#765BA7", "image": "manouba.jpg",
     "seed": "Musée militaire de mannouba.jpg",
     "query": "Manouba museum Tunisia", "note": None},
    {"slug": "nabeul", "name": "Nabeul", "lat": 36.4561, "lon": 10.7376,
     "accent": "#E85D75", "image": "nabeul.jpg", "seed": None,
     "query": "Nabeul pottery Tunisia", "note": None},
    {"slug": "zaghouan", "name": "Zaghouan", "lat": 36.4029, "lon": 10.1429,
     "accent": "#4C956C", "image": "zaghouan.jpg",
     "seed": "Zaghouan City Mountain.jpg",
     "query": "Zaghouan mountain city", "note": None},
    {"slug": "bizerte", "name": "Bizerte", "lat": 37.2746, "lon": 9.8739,
     "accent": "#00838A", "image": "bizerte.jpg", "seed": None,
     "query": "Bizerte old port Tunisia", "note": None},
    {"slug": "beja", "name": "Béja", "lat": 36.7256, "lon": 9.1817,
     "accent": "#A05A2C", "image": "beja.jpg", "seed": None,
     "query": "Dougga Tunisia Roman capitol", "note": "Région de Béja"},
    {"slug": "jendouba", "name": "Jendouba", "lat": 36.5011, "lon": 8.7803,
     "accent": "#2E6E4E", "image": "jendouba.jpg",
     "seed": "Tabarka aiguille1.JPG",
     "query": "Tabarka aiguilles rocks Tunisia", "note": "Région de Jendouba"},
    {"slug": "le-kef", "name": "Le Kef", "lat": 36.1742, "lon": 8.7049,
     "accent": "#946B2D", "image": "le-kef.jpg", "seed": None,
     "query": "Le Kef kasbah Tunisia", "note": None},
    {"slug": "siliana", "name": "Siliana", "lat": 36.0849, "lon": 9.3708,
     "accent": "#4A6FA5", "image": "siliana.jpg",
     "seed": "Siliana-centre.jpg",
     "query": "Siliana city Tunisia", "note": None},
    # --- Center ---
    {"slug": "sousse", "name": "Sousse", "lat": 35.8256, "lon": 10.6084,
     "accent": "#1F7A8C", "image": "sousse.jpg", "seed": None,
     "query": "Sousse ribat medina Tunisia", "note": None},
    {"slug": "monastir", "name": "Monastir", "lat": 35.7780, "lon": 10.8262,
     "accent": "#35507C", "image": "monastir.jpg",
     "seed": "Ribat de Monastir 111.jpg",
     "query": "Monastir ribat Tunisia", "note": None},
    {"slug": "mahdia", "name": "Mahdia", "lat": 35.5047, "lon": 11.0622,
     "accent": "#147BA6", "image": "mahdia.jpg", "seed": None,
     "query": "Mahdia skifa kahla Tunisia", "note": None},
    {"slug": "kairouan", "name": "Kairouan", "lat": 35.6781, "lon": 10.0963,
     "accent": "#A63D40", "image": "kairouan.jpg", "seed": None,
     "query": "Kairouan great mosque Tunisia", "note": None},
    {"slug": "sfax", "name": "Sfax", "lat": 34.7406, "lon": 10.7603,
     "accent": "#7C3A5E", "image": "sfax.jpg", "seed": None,
     "query": "Sfax medina walls Tunisia", "note": None},
    {"slug": "kasserine", "name": "Kasserine", "lat": 35.1676, "lon": 8.8365,
     "accent": "#5C7291", "image": "kasserine.jpg",
     "seed": "Trois temples de Sbeitla.jpg",
     "query": "Sbeitla temples Tunisia", "note": "Région de Kasserine"},
    {"slug": "sidi-bouzid", "name": "Sidi Bouzid", "lat": 35.0382, "lon": 9.4849,
     "accent": "#B4552D", "image": "sidi-bouzid.jpg",
     "seed": "Sidi Bouzid.jpg",
     "query": "Sidi Bouzid city Tunisia", "note": None},
    # --- South ---
    {"slug": "gabes", "name": "Gabès", "lat": 33.8815, "lon": 10.0982,
     "accent": "#3E8914", "image": "gabes.jpg",
     "seed": "Palmeraie gabès2.jpg",
     "query": "Gabes oasis Tunisia", "note": None},
    {"slug": "gafsa", "name": "Gafsa", "lat": 34.4250, "lon": 8.7842,
     "accent": "#8C6A39", "image": "gafsa.jpg", "seed": None,
     "query": "Gafsa Roman pools Tunisia", "note": None},
    {"slug": "tozeur", "name": "Tozeur", "lat": 33.9197, "lon": 8.1335,
     "accent": "#C77B21", "image": "tozeur.jpg",
     "seed": "Tozeur Oasis at sunset.jpg",
     "query": "Tozeur oasis Tunisia", "note": None},
    {"slug": "kebili", "name": "Kébili", "lat": 33.7044, "lon": 8.9690,
     "accent": "#C24C64", "image": "kebili.jpg",
     "seed": "Entrée Oasis-Kebili.JPG",
     "query": "Kebili oasis Tunisia", "note": None},
    {"slug": "medenine", "name": "Médenine", "lat": 33.3549, "lon": 10.5055,
     "accent": "#6E5E85", "image": "medenine.jpg",
     "seed": "Medenine-stegop-06.jpg",
     "query": "Medenine ksar Tunisia", "note": None},
    {"slug": "tataouine", "name": "Tataouine", "lat": 32.9297, "lon": 10.4517,
     "accent": "#A34E2A", "image": "tataouine.jpg", "seed": None,
     "query": "Ksar Ouled Soltane Tataouine Tunisia", "note": None},
]

_BY_SLUG = {c["slug"]: c for c in CITIES}


def get_city(slug: str):
    """Return the city dict for slug, or None."""
    return _BY_SLUG.get(slug)


def nearest_city(lat: float, lon: float) -> dict:
    """Return the catalog city closest to (lat, lon) using haversine distance."""
    import math

    def dist(c: dict) -> float:
        phi1, phi2 = math.radians(lat), math.radians(c["lat"])
        dphi = math.radians(c["lat"] - lat)
        dlmb = math.radians(c["lon"] - lon)
        a = (math.sin(dphi / 2) ** 2
             + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2)
        return 2 * math.asin(math.sqrt(a))

    return min(CITIES, key=dist)
