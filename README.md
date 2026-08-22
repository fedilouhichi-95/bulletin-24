# Bulletin 24

Bulletin météo imprimé pour les 24 chefs-lieux de Tunisie. Chaque ville a sa page,
son encre, sa photo libre de droits — les données viennent d'Open-Meteo, le tout tient
dans un conteneur Docker déployé gratuitement sur Render.

**En ligne** : <https://bulletin-24.onrender.com>

| Choix de ville | Le bulletin d'une ville |
|---|---|
| ![Choix de ville](docs/img/picker.png) | ![Bulletin Mahdia](docs/img/mahdia.png) |

## Fonctionnement

```text
navigateur ──▶ Flask (rendu serveur, Jinja)
                 │
                 ├─ cookie « city » absent ? ──▶ /choisir-ville (24 villes)
                 │                              miniatures WebP + placeholders LQIP
                 │
                 └─ cookie présent ──▶ bulletin de la ville
                        │
                         ├─ Open-Meteo ×2 en parallèle (ThreadPoolExecutor)
                         │    ├─ météo courante + prévisions 5 jours de la ville
                         │    └─ températures des 23 autres villes (1 appel groupé)
                         │  cache mémoire TTL 30 min · stale-while-revalidate
                         │  (sur l'appel principal ; le bandeau se masque si échec)
                        │
                        └─ HTML rendu (CSS inliné, Brotli) + WebP (héros/vignette/LQIP base64)
```

Un seul état utilisateur : le cookie `city`, lu côté serveur. Aucune base de
données, aucun JavaScript obligatoire — le JS ne sert qu'à la géolocalisation.

## Choix techniques

| Choix | Alternative écartée | Pourquoi |
|---|---|---|
| Rendu serveur Flask | SPA React/Vue | pages testables avec `pytest` sans navigateur, JS réduit au strict minimum, un seul processus à déployer |
| Cookie `city` lu par le serveur | localStorage ou BDD | l'état vit là où la page est rendue ; redirection et rendu en une requête |
| Open-Meteo | OpenWeatherMap | aucune clé API → aucun secret à gérer ni quota à surveiller côté client |
| Cache mémoire + stale-while-revalidate | Redis/Celery | un dict horodaté suffit à cette échelle ; Redis serait un service de plus à payer et opérer |
| Photos Wikimedia Commons | banques d'images libres | licences vérifiables, métadonnées exploitables par API, provenance tracée dans `data/image_credits.json` |
| Docker + Render free tier | VPS dès le départ | coût 0 € validé, `render.yaml` versionné, migration vers un VPS possible sans toucher au code |

## Performance mesurée

| Métrique | Avant | Après |
|---|---|---|
| Chargement du choix de ville | ~6 Mo de JPG pleine résolution | **~0,9 Mo** (WebP 3 tailles + LQIP) |
| HTML servi | 10 Ko brut | **8,3 Ko** compressé Brotli, CSS inliné |
| Requêtes bloquantes au rendu | 2 feuilles CSS | **0** |
| Attente API visible | possible (cache expiré) | jamais (stale-while-revalidate) |
| Temps de réponse `/` | — | **0,41 s ± 0,02 s** |

## Démarrage local

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py          # http://localhost:5000
```

Tests et lint :

```bash
pytest
ruff check .
```

## Structure du dépôt

```text
app/                    application Flask (factory, routes, services, templates, statiques)
  services/cities.py    catalogue des 24 villes — source unique de vérité
  services/weather.py   client Open-Meteo, cache, labels WMO en français
docs/
  STORY.md              étude de cas : les incidents réels et leurs correctifs
  SPEC.md               périmètre fonctionnel et critères d'acceptation
  AGENTS.md             conventions du projet
  PROGRESS.md           journal de bord technique
scripts/
  fetch_images.py       téléchargement idempotent des photos Commons + crédits
  optimize_images.py    pipeline Pillow : héros / vignette / LQIP WebP
tests/                  suite pytest (catalogue, parsing, cache, routes, crédits)
wsgi.py                 point d'entrée gunicorn (utilisé par le Dockerfile)
Dockerfile · docker-compose.yml · render.yaml · .github/workflows/ci.yml
```

## CI/CD

Chaque push sur `main` déclenche GitHub Actions :
ruff → pytest → build Docker → **smoke test runtime** (le conteneur démarre
réellement et doit répondre HTTP 200). Puis Render redéploie automatiquement.
Un cron externe maintient l'instance gratuite éveillée.

---

L'histoire complète — contraintes, incidents, diagnostics et correctifs — se lit
dans [docs/STORY.md](docs/STORY.md).
