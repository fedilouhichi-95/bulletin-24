# L'histoire de Bulletin 24

*Du premier message à l'utilisateur (« je veux créer une météo app avec une stack
simple ») au site en production — le vrai récit, avec les choix, les bugs et les leçons.*

---

## 1. Le brief : un débutant veut tout apprendre

Tout part d'une demande simple : une app météo web, de A à Z jusqu'au déploiement,
avec la stack d'un débutant. L'interrogatoire initial a fixé le cadre :

- **Flask** plutôt qu'un framework JavaScript : un seul langage, un seul processus,
  et des pages rendues côté serveur — plus simple à comprendre ligne par ligne.
- **Aucune base de données, aucune authentification** : une app météo n'en a pas
  besoin en v1. Refuser des fonctionnalités fait partie de la conception.
- **API Open-Meteo** : gratuite, sans clé, sans inscription — zéro secret à gérer.
- Objectif pédagogique assumé : apprendre aussi le **DevOps** (Git, CI/CD, Docker).

Décision structurante n°1 : le choix de la ville est stocké dans un **cookie** lu par
le serveur, pas dans le localStorage. Résultat : Flask rend directement la bonne page,
et tout est testable avec `pytest` sans navigateur.

## 2. La direction artistique : refuser l'interface générique

Le cahier des charges était explicite : *pas une interface générée par IA*. Les apps
météo ressemblent toutes à des cartes dégradés bleu-violet. Nous avons choisi
l'inverse : chaque ville devient une **page d'almanach sérigraphiée**.

L'ancrage visuel « Lo-Fi » impose ses tokens, et nous les avons tenus partout :

- papier jaune `#E8E0C0`, encre presque noire ;
- polices système mélangées délibérément (Times / Helvetica / Courier) ;
- photos traitées en demi-teinte, éléments inclinés de quelques degrés ;
- malencontre risographique (`text-shadow` rose/cyan) sur les grands titres ;
- une **couleur d'encre par ville** (port bleu de Bizerte, ocre de Tozeur…).

Ce cadre a une vertu cachée : il contraint. Chaque nouvelle fonctionnalité devait
ressembler à un imprimé, pas à un dashboard.

## 3. Les 24 villes : sourcing honnête sur Wikimedia Commons

La Tunisie compte 24 gouvernorats. Il fallait pour chacun : nom français, coordonnées
(l'API géocodage devient inutile), couleur d'encre, et **une photo libre de droits**.

Méthode : requêtes ciblées contre l'API de Wikimedia Commons, vérification manuelle
des résultats, puis un script `fetch_images.py` qui télécharge, enregistre les crédits
(photographe, licence) et reste rejouable.

### Bug n°1 — le mur des 429

Premier lancement : 2 téléchargements puis **429 Too Many Requests** partout.
Correctif dans le script :

- pause de politesse entre chaque ville ;
- réessais avec backoff croissant (15 s → 30 s → 60 s) uniquement sur les 429.

### Bug n°2 — le bug dans mon propre correctif

Après ajout du backoff : `got multiple values for keyword argument 'timeout'`.
J'avais passé `timeout` deux fois (dans la fonction et via `**kwargs`).
Correction : un seul paramètre explicite. *Leçon : relire son patch avant de relancer.*

### Les villes « introuvables »

Plusieurs recherches renvoyaient n'importe quoi : Ben Arous donnait la *rue*
Sidi Ben Arous de la médina de Tunis ; Kasserine ne proposait que des cartes
administratives ; Ariana rien du tout. Trois réponses différentes :

1. **Photos de région assumées**, légendées honnêtement (« Région de Kasserine —
   Sbeïtla ») quand un site emblématique existe : Dougga pour Béja, Tabarka pour
   Jendouba, Hammam-Lif pour Ben Arous.
2. **Variante typographique** prévue pour Ariana (monogramme géant) — jamais
   nécessaire finalement.
3. **Une dernière recherche ciblée** a trouvé la photo parfaite : le palais Ben Ayed
   et la municipalité de l'Ariana. Bilan final : **24/24 photos libres**.

### Bug n°3 — les requêtes trop vagues

« Monastir ribas bourguiba » (faute incluse) ne donnait rien ; « Gabès » renvoyait
une panoramique de 1992 hors sujet. Solution : des **seeds exacts** vérifiés à la main
(`Ribat de Monastir 111.jpg`…) que le script essaie avant toute recherche.

## 4. Le bug qui a tout appris : construire ≠ exécuter ⭐

Le jour du déploiement sur Render, la construction Docker réussit… puis :

```text
sh: 1: Syntax error: "(" unexpected
==> Exited with status 2
```

Cause racine : le `CMD` du Dockerfile contenait `gunicorn … app:create_app()`.
Le shell `dash` interprète les parenthèses non protégées comme une définition de
fonction. La CI était verte parce qu'elle **construisait** l'image sans jamais
l'**exécuter** — et mes tests locaux utilisaient gunicorn directement, en contournant
le CMD.

Correctif en deux temps :

1. Un point d'entrée `wsgi.py` (`app = create_app()`) et un `CMD` sans parenthèses,
   qui honore en bonus `WEB_CONCURRENCY` imposé par Render.
2. **Un smoke test runtime dans la CI** : après le build, GitHub Actions lance
   vraiment le conteneur et attend un HTTP 200. Ce type de panne ne peut plus
   atteindre la production.

*Leçon retenue : une pipeline qui construit sans démarrer ne teste pas le déploiement.*

## 5. Performance : d'un site lent à un site instantané

Premier retour utilisateur : « le site met du temps ». Diagnostic mesuré, pas deviné :
le HTML répondait en 0,4 s, mais le choix de ville téléchargeait **6 Mo de photos**
pleine résolution pour des vignettes de 150 px, sur une instance gratuite à 0,1 CPU.

Pipeline mis en place (script Pillow, aucune dépendance exotique) :

| Variante | Taille | Usage |
|---|---|---|
| WebP héros 960 px | ~90 Ko | page almanach |
| WebP miniature 480 px | ~25 Ko | cartes du picker |
| WebP 20 px flouté (LQIP) | ~150 o | embarqué en base64 dans le HTML |

Résultats mesurés en production : picker passé de **6 Mo à ~0,9 Mo**, HTML de 10 Ko
à **8,3 Ko Brotli**, cache statique d'un an, CSS inliné (zéro requête bloquante),
appels Open-Meteo parallélisés, et *stale-while-revalidate* : plus jamais d'attente
d'API visible.

## 6. DevOps à coût zéro

- **CI GitHub Actions** : ruff → pytest → build Docker → smoke test runtime.
- **Render free tier** via blueprint `render.yaml` : redéploiement automatique à
  chaque push sur `main` (CD inclus).
- **Keep-alive** : un cron externe visite `/choisir-ville` toutes les 10 minutes
  pour que l'instance gratuite ne s'endorme jamais (~730 h des 750 h offertes).
- Coût total du projet : **0 €**.

Compromis assumés et documentés : instance qui dort si le pinger s'arrête.
L'attribution photo, un temps retirée de l'interface à la demande du propriétaire,
a ensuite été rétablie sur la page `/credits` — la majorité des images étant sous
licence CC BY-SA, le crédit visible n'était pas négociable.

## 7. Bilan réflexif

**À refaire pareil :** SSR + cookie, catalogue statique unique (`cities.py`),
tests sans réseau, design contraint par un ancrage fort, documentation écrite
pendant le projet (`PROGRESS.md`) et non après coup.

**À faire différemment :** tester le conteneur en local dès son écriture (le bug
de parenthèses aurait sauté en 10 secondes) ; écrire les seeds Commons vérifiés
*d'avant* la première passe de téléchargement ; compresser les images dès le
premier commit plutôt qu'après retour utilisateur.

---

*Projet réalisé comme exercice complet : produit, design, backend, tests, CI/CD,
déploiement et performance — du premier message au site en ligne.*
