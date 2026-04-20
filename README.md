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

---

## Informations de paiement (test)

Le service de paiement externe est hébergé à l'UQAC :

```
URL : https://dimensweb.uqac.ca/~jgnault/shops/pay/
```

### Carte de crédit valide (pour les tests)

| Champ              | Valeur               |
|--------------------|----------------------|
| `name`             | `John Doe`           |
| `number`           | `4242 4242 4242 4242` |
| `expiration_month` | `9`                  |
| `expiration_year`  | `2026`               |
| `cvv`              | `123`                |

> Toute autre combinaison peut être refusée par le service distant.

### Format de la requête de paiement (`PUT /order/<id>`)

```json
{
  "credit_card": {
    "name": "John Doe",
    "number": "4242 4242 4242 4242",
    "expiration_month": 9,
    "expiration_year": 2026,
    "cvv": "123"
  }
}
```

> Le paiement est traité en arrière-plan par le worker RQ. La réponse immédiate est `202 Accepted`.  
> Interroger `GET /order/<id>` jusqu'à obtenir un statut `200` avec `"paid": true`.

---

## Adresse de livraison (pour les tests)

Aucune adresse spécifique n'est imposée par l'énoncé. Voici un exemple valide :

| Champ         | Valeur          |
|---------------|-----------------|
| `country`     | `Canada`        |
| `address`     | `123 Rue Test`  |
| `postal_code` | `G7H 0A1`       |
| `city`        | `Chicoutimi`    |
| `province`    | `QC`            |

Provinces acceptées : `QC`, `ON`, `AB`, `BC`, `NS`

### Format de la requête d'adresse (`PUT /order/<id>`)

```json
{
  "order": {
    "email": "test@example.com",
    "shipping_information": {
      "country": "Canada",
      "address": "123 Rue Test",
      "postal_code": "G7H 0A1",
      "city": "Chicoutimi",
      "province": "QC"
    }
  }
}
```

> Les informations client (adresse) et le paiement doivent être envoyés dans **deux requêtes séparées**.
