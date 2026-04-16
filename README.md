# INF349 — Projet de Session Flask (Remise 2)

**Nom :** KELLY NOELLE MAPOUE PEKEKO  
**Code permanent :** MAPK22510200

---

## Description

Application Flask REST pour la gestion de commandes Internet avec paiement en arrière-plan.  
Développée avec Python 3.12, Flask 2.3.3, Peewee 3.16.2, PostgreSQL, Redis et RQ.

---

## Fonctionnalités

### API REST
- `GET /` — Liste de tous les produits
- `POST /order` — Création de commande (un ou plusieurs produits)
- `GET /order/<id>` — Consultation de commande (avec cache Redis)
- `PUT /order/<id>` — Mise à jour des informations client OU paiement (séparés)

### Interface utilisateur HTML
- `GET /ui` — Page boutique : liste des produits et création de commande
- `GET /ui/order/<id>` — Page commande : détails, formulaire livraison, formulaire paiement

### Résilience
- Les commandes payées sont mises en cache dans Redis
- `GET /order/<id>` vérifie Redis en premier et fonctionne sans PostgreSQL pour les commandes mises en cache

### Calculs automatiques
- Frais d'expédition : 5 $ (≤500 g), 10 $ (500 g–2 kg), 25 $ (≥2 kg)
- Taxes provinciales : QC 15 %, ON 13 %, AB 5 %, BC 12 %, NS 14 %

---

## Prérequis

- Python 3.6+
- PostgreSQL 12
- Redis 5
- Docker (optionnel)

---

## Variables d'environnement

| Variable       | Description                         | Exemple                  |
|----------------|-------------------------------------|--------------------------|
| `DB_HOST`      | Hôte PostgreSQL                     | `localhost`              |
| `DB_USER`      | Nom d'utilisateur PostgreSQL        | `user`                   |
| `DB_PASSWORD`  | Mot de passe PostgreSQL             | `pass`                   |
| `DB_PORT`      | Port PostgreSQL                     | `5432`                   |
| `DB_NAME`      | Nom de la base de données           | `api8inf349`             |
| `REDIS_URL`    | URL de connexion Redis              | `redis://localhost`      |

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Initialisation de la base de données

**Windows CMD :**
```cmd
SET FLASK_APP=api8inf349& SET DB_HOST=localhost& SET DB_USER=user& SET DB_PASSWORD=pass& SET DB_PORT=5432& SET DB_NAME=api8inf349& SET REDIS_URL=redis://localhost& flask init-db
```

**Windows PowerShell :**
```powershell
$env:FLASK_APP="api8inf349"; $env:DB_HOST="localhost"; $env:DB_USER="user"; $env:DB_PASSWORD="pass"; $env:DB_PORT="5432"; $env:DB_NAME="api8inf349"; $env:REDIS_URL="redis://localhost"; flask init-db
```

**Linux / macOS :**
```bash
FLASK_APP=api8inf349 DB_HOST=localhost DB_USER=user DB_PASSWORD=pass DB_PORT=5432 DB_NAME=api8inf349 REDIS_URL=redis://localhost flask init-db
```

> Cette commande crée les tables et récupère les produits depuis le service distant.

---

## Démarrage de l'application

**Windows CMD :**
```cmd
SET FLASK_APP=api8inf349& SET DB_HOST=localhost& SET DB_USER=user& SET DB_PASSWORD=pass& SET DB_PORT=5432& SET DB_NAME=api8inf349& SET REDIS_URL=redis://localhost& flask run
```

**Windows PowerShell :**
```powershell
$env:FLASK_APP="api8inf349"; $env:DB_HOST="localhost"; $env:DB_USER="user"; $env:DB_PASSWORD="pass"; $env:DB_PORT="5432"; $env:DB_NAME="api8inf349"; $env:REDIS_URL="redis://localhost"; flask run
```

**Linux / macOS :**
```bash
FLASK_APP=api8inf349 DB_HOST=localhost DB_USER=user DB_PASSWORD=pass DB_PORT=5432 DB_NAME=api8inf349 REDIS_URL=redis://localhost flask run
```

L'application sera accessible sur : http://localhost:5000  
L'interface HTML sera accessible sur : http://localhost:5000/ui

---

## Démarrage du worker RQ

Dans un terminal séparé :

**Windows CMD :**
```cmd
SET FLASK_APP=api8inf349& SET DB_HOST=localhost& SET DB_USER=user& SET DB_PASSWORD=pass& SET DB_PORT=5432& SET DB_NAME=api8inf349& SET REDIS_URL=redis://localhost& flask worker
```

**Windows PowerShell :**
```powershell
$env:FLASK_APP="api8inf349"; $env:DB_HOST="localhost"; $env:DB_USER="user"; $env:DB_PASSWORD="pass"; $env:DB_PORT="5432"; $env:DB_NAME="api8inf349"; $env:REDIS_URL="redis://localhost"; flask worker
```

**Linux / macOS :**
```bash
FLASK_APP=api8inf349 DB_HOST=localhost DB_USER=user DB_PASSWORD=pass DB_PORT=5432 DB_NAME=api8inf349 REDIS_URL=redis://localhost flask worker
```

---

## Docker

### Lancer les services PostgreSQL et Redis

```bash
docker-compose up -d
```

Cela démarre :
- PostgreSQL 12 sur le port 5432 (avec volume persistant)
- Redis 5 sur le port 6379

### Construire l'image de l'application

```bash
docker build -t api8inf349 .
```

### Lancer l'application dans Docker

```bash
docker run -e REDIS_URL=redis://host.docker.internal \
           -e DB_HOST=host.docker.internal \
           -e DB_USER=user \
           -e DB_PASSWORD=pass \
           -e DB_PORT=5432 \
           -e DB_NAME=api8inf349 \
           -p 5000:5000 \
           api8inf349
```

> Utiliser `host.docker.internal` pour communiquer avec PostgreSQL/Redis lancés via docker-compose depuis un conteneur.

---

## Structure du projet

```
inf349/
├── __init__.py          # Factory Flask
├── models.py            # Modèles Peewee (PostgreSQL)
├── routes.py            # Routes API REST (JSON)
├── ui.py                # Routes interface HTML
├── services.py          # Logique métier
├── tasks.py             # Tâches RQ (paiement en arrière-plan)
├── utils.py             # Validation, calculs, formatage
├── errors.py            # Gestion centralisée des erreurs
├── commands.py          # Commandes Flask CLI (init-db, worker)
└── templates/
    ├── index.html       # Page boutique (liste produits + création commande)
    └── order.html       # Page commande (détails + livraison + paiement)

Fichiers racine :
├── Dockerfile           # Image Docker de l'application
├── docker-compose.yml   # Services PostgreSQL 12 + Redis 5
├── requirements.txt     # Dépendances Python
├── CODES-PERMANENTS     # Code permanent étudiant
└── README.md
```

---

## Codes d'erreur HTTP

| Code | Signification                                        |
|------|------------------------------------------------------|
| 200  | Succès                                               |
| 202  | Paiement accepté / en cours de traitement            |
| 302  | Commande créée, redirection vers GET /order/<id>     |
| 404  | Ressource introuvable                                |
| 409  | Conflit — commande en cours de paiement              |
| 422  | Erreur de validation (champs manquants, hors stock…) |

---

## Codes d'erreur métier

| Code                    | Signification                             |
|-------------------------|-------------------------------------------|
| `missing-fields`        | Champs obligatoires manquants             |
| `out-of-inventory`      | Produit non disponible en stock           |
| `already-paid`          | Commande déjà payée                       |
| `payment-in-progress`   | Paiement déjà en cours                   |
| `card-declined`         | Carte de crédit refusée par le service    |
