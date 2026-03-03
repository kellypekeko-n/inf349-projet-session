# INF349 - Projet de Session - Application Web de Commandes

## Description

Ce projet est une application Web Flask développée pour le cours INF349 à l'UQAC. L'application gère des commandes Internet avec une API REST complète et des services de paiement externes.

## Fonctionnalités

- **Gestion des produits** : Récupération et stockage local des produits depuis un service distant
- **Création de commandes** : API pour créer des commandes avec validation d'inventaire
- **Calculs automatiques** : Prix d'expédition et taxes selon la province
- **Intégration paiement** : Communication avec service de paiement distant
- **Gestion d'erreurs** : Validation complète et messages d'erreur standards

## Architecture

### Structure du Projet

```
inf349/
├── __init__.py          # Initialisation Flask et configuration
├── config.py            # Configuration production
├── models.py            # Modèles Peewee (ORM)
├── routes.py            # Routes API REST
├── services.py          # Logique métier
├── utils.py             # Utilitaires et validation
├── errors.py            # Gestion d'erreurs centralisée
├── commands.py          # Commandes CLI Flask
└── tests/               # Tests complets
    ├── __init__.py
    ├── conftest.py      # Configuration tests
    ├── test_products.py # Tests produits
    ├── test_orders.py   # Tests commandes
    ├── test_payment.py  # Tests paiements
    └── test_utils.py    # Tests utilitaires
```

### Modèles de Données

- **Product** : Informations des produits
- **Order** : Commandes avec calculs automatiques
- **ShippingInformation** : Informations de livraison
- **CreditCard** : Cartes de crédit (masquées)
- **Transaction** : Transactions de paiement

### Services Externes

- **Service Produits** : `http://dimensweb.uqac.ca/~jgnault/shops/products/`
- **Service Paiement** : `http://dimensweb.uqac.ca/~jgnault/shops/pay/`

## Installation

### Prérequis

- Python 3.6+ (recommandé: 3.11)
- pip (gestionnaire de paquets Python)

### Étapes d'Installation

1. **Cloner le projet**
   ```bash
   git clone <repository-url>
   cd Project_tech_web1
   ```

2. **Créer environnement virtuel**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialiser la base de données**
   ```bash
   # Windows
   set FLASK_DEBUG=True
   set FLASK_APP=inf349
   flask init-db
   
   # Linux/Mac
   export FLASK_DEBUG=True
   export FLASK_APP=inf349
   flask init-db
   ```

## Utilisation

### Démarrer l'Application

```bash
# Windows
set FLASK_DEBUG=True
set FLASK_APP=inf349
flask run

# Linux/Mac
export FLASK_DEBUG=True
export FLASK_APP=inf349
flask run
```

L'application sera accessible sur `http://localhost:5000`

### API Endpoints

#### GET /
Retourne la liste complète des produits

**Response:**
```json
{
  "products": [
    {
      "id": 1,
      "name": "Brown eggs",
      "description": "Raw organic brown eggs in a basket",
      "price": 28.1,
      "in_stock": true,
      "weight": 400,
      "image": "0.jpg"
    }
  ]
}
```

#### POST /order
Crée une nouvelle commande

**Request:**
```json
{
  "product": {
    "id": 1,
    "quantity": 2
  }
}
```

**Response:** `302 Found` avec header `Location: /order/<order_id>`

#### GET /order/<id>
Retourne les détails d'une commande

**Response:**
```json
{
  "order": {
    "id": 1,
    "total_price": 2000,
    "total_price_tax": 2300.00,
    "email": "client@example.com",
    "credit_card": {},
    "shipping_information": {
      "country": "Canada",
      "address": "123 rue Principale",
      "postal_code": "G7X 3Y7",
      "city": "Chicoutimi",
      "province": "QC"
    },
    "paid": false,
    "transaction": {},
    "product": {
      "id": 1,
      "quantity": 2
    },
    "shipping_price": 500
  }
}
```

#### PUT /order/<id>
Met à jour les informations client ou traite le paiement

**Informations client:**
```json
{
  "order": {
    "email": "client@example.com",
    "shipping_information": {
      "country": "Canada",
      "address": "123 rue Principale",
      "postal_code": "G7X 3Y7",
      "city": "Chicoutimi",
      "province": "QC"
    }
  }
}
```

**Paiement:**
```json
{
  "credit_card": {
    "name": "John Doe",
    "number": "4242 4242 4242 4242",
    "expiration_year": 2024,
    "expiration_month": 9,
    "cvv": "123"
  }
}
```

## Calculs

### Prix d'Expédition

- ≤ 500g : 5$ (500 cents)
- 500g - 2kg : 10$ (1000 cents)
- ≥ 2kg : 25$ (2500 cents)

### Taxes par Province

- Québec (QC) : 15%
- Ontario (ON) : 13%
- Alberta (AB) : 5%
- Colombie-Britannique (BC) : 12%
- Nouvelle-Écosse (NS) : 14%

## Tests

### Exécuter tous les tests
```bash
pytest
```

### Exécuter avec couverture
```bash
pytest --cov=inf349
```

### Tests spécifiques
```bash
pytest inf349/tests/test_orders.py
pytest inf349/tests/test_payment.py
```

## Gestion des Erreurs

L'application utilise une gestion d'erreurs centralisée avec les codes suivants :

- **missing-fields** : Champs obligatoires manquants
- **out-of-inventory** : Produit non disponible
- **already-paid** : Commande déjà payée
- **card-declined** : Carte de crédit refusée

## Développement

### Commandes Utiles

```bash
# Initialiser base de données
flask init-db

# Récupérer produits (test)
flask fetch-products

# Tests avec verbosity
pytest -v

# Tests avec couverture détaillée
pytest --cov=inf349 --cov-report=html
```

### Normes de Code

- PEP8 pour le style Python
- Séparation claire des responsabilités
- Tests complets pour toutes les fonctionnalités
- Documentation des fonctions critiques

## Performance et Résilience

### Optimisations

- **Cache local** : Produits récupérés une seule fois au démarrage
- **Transactions DB** : Opérations de paiement atomiques
- **Validation précoce** : Erreurs détectées avant traitements lourds
- **Timeouts réseau** : Gestion des services externes

### Résilience

- **Gestion d'erreurs réseau** : Services externes indisponibles
- **Validation stricte** : Données corrompues rejetées
- **Rollback automatique** : Transactions annulées en cas d'erreur
- **Logs détaillés** : Traçabilité des incidents

## Sécurité

### Mesures Implémentées

- **Masquage cartes** : Seuls first/last digits stockés
- **Validation stricte** : Injection SQL évitée via ORM
- **HTTPS recommandé** : Production avec SSL/TLS
- **Pas de données sensibles** : Pas de mots de passe en clair

### Améliorations Futures

- **Rate limiting** : Limiter requêtes par IP
- **CSRF protection** : Formulaires sécurisés
- **Input sanitization** : Nettoyage entrées utilisateur
- **Audit logging** : Traçabilité actions sensibles

## Déploiement

### Production

1. **Configuration environnement** : Variables d'environnement
2. **Base de données** : SQLite remplacé par PostgreSQL si besoin
3. **Serveur WSGI** : Gunicorn ou uWSGI
4. **Reverse proxy** : Nginx ou Apache
5. **Monitoring** : Logs et métriques

### Docker (Optionnel)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]
```

## Contribution

1. Fork du projet
2. Branche feature : `git checkout -b feature/nouvelle-fonctionnalite`
3. Commit : `git commit -am 'Ajout nouvelle fonctionnalité'`
4. Push : `git push origin feature/nouvelle-fonctionnalite`
5. Pull Request

## Licence

Projet éducatif - INF349 UQAC

## Contact

- Équipe de développement
- Enseignant : Jean-Guy Nault
- Cours : INF349 - Développement Web
