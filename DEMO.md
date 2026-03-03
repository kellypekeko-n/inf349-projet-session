# Démonstration INF349 - Projet de Session

## Guide de Démonstration Rapide

Ce document guide la démonstration du projet INF349 pour la première remise.

## Prérequis

```bash
# Installation des dépendances
pip install -r requirements.txt

# Initialisation de la base de données
python -c "import sys; sys.path.insert(0, '.'); from inf349 import create_app; app = create_app(); app.app_context().push(); from inf349.models import initialize_db; from inf349 import db; initialize_db(db); print('Database initialized')"
```

## Lancement de l'Application

```bash
# Démarrer le serveur Flask
export FLASK_DEBUG=True
export FLASK_APP=inf349
flask run
```

L'application sera accessible sur `http://localhost:5000`

## Scénario de Démonstration

### 1. Récupération des Produits

```bash
# Obtenir la liste complète des produits
curl -X GET http://localhost:5000/
```

**Résultat attendu**:
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

### 2. Création d'une Commande

```bash
# Créer une nouvelle commande
curl -X POST http://localhost:5000/order \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "id": 1,
      "quantity": 2
    }
  }'
```

**Résultat attendu**:
- Status: `302 Found`
- Header: `Location: /order/1`

### 3. Consultation d'une Commande

```bash
# Consulter la commande créée
curl -X GET http://localhost:5000/order/1
```

**Résultat attendu**:
```json
{
  "order": {
    "id": 1,
    "total_price": 5620,
    "total_price_tax": 7613.0,
    "email": null,
    "credit_card": {},
    "shipping_information": {},
    "paid": false,
    "transaction": {},
    "product": {
      "id": 1,
      "quantity": 2
    },
    "shipping_price": 1000
  }
}
```

### 4. Mise à Jour des Informations Client

```bash
# Ajouter les informations client
curl -X PUT http://localhost:5000/order/1 \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Résultat attendu**: Status `200 OK` avec mise à jour des taxes (15% pour QC)

### 5. Traitement du Paiement

```bash
# Traiter le paiement (carte valide)
curl -X PUT http://localhost:5000/order/1 \
  -H "Content-Type: application/json" \
  -d '{
    "credit_card": {
      "name": "John Doe",
      "number": "4242 4242 4242 4242",
      "expiration_year": 2024,
      "expiration_month": 9,
      "cvv": "123"
    }
  }'
```

**Résultat attendu**: Status `200 OK` avec informations de paiement masquées

## Scénarios d'Erreur

### 1. Produit Hors Stock

```bash
# Tenter de commander un produit hors stock
curl -X POST http://localhost:5000/order \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "id": 4,  # Produit hors stock
      "quantity": 1
    }
  }'
```

**Résultat attendu**:
```json
{
  "errors": {
    "product": {
      "code": "out-of-inventory",
      "name": "Le produit demandé n'est pas en inventaire"
    }
  }
}
```

### 2. Champs Manquants

```bash
# Commande avec champs manquants
curl -X POST http://localhost:5000/order \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "id": 1
      // quantité manquante
    }
  }'
```

**Résultat attendu**: Erreur `422 Unprocessable Entity`

### 3. Paiement Sans Informations Client

```bash
# Tenter de payer sans informations client
curl -X PUT http://localhost:5000/order/1 \
  -H "Content-Type: application/json" \
  -d '{
    "credit_card": {
      "name": "John Doe",
      "number": "4242 4242 4242 4242",
      "expiration_year": 2024,
      "expiration_month": 9,
      "cvv": "123"
    }
  }'
```

**Résultat attendu**: Erreur `422` avec message "informations du client nécessaires"

## Tests Automatisés

```bash
# Exécuter tous les tests
python run_tests.py
```

**Résultat attendu**: `✅ All tests passed!`

## Points Clés à Démontrer

### 1. Architecture Propre
- **Séparation des responsabilités**: Routes, Services, Utils, Models
- **Code modulaire**: Chaque fichier a un rôle précis
- **Maintenabilité**: Structure claire et documentée

### 2. API REST Complète
- **GET /**: Liste des produits (incluant hors stock)
- **POST /order**: Création avec validation
- **GET /order/<id>**: Consultation avec calculs
- **PUT /order/<id>**: Mise à jour client ET paiement

### 3. Calculs Automatiques
- **Prix d'expédition**: Selon poids total
- **Taxes provinciales**: QC 15%, ON 13%, AB 5%, BC 12%, NS 14%
- **Prix total**: Automatique et précis

### 4. Gestion d'Erreurs Robuste
- **Validation des entrées**: Champs obligatoires
- **Erreurs métier**: Stock disponible, quantité valide
- **Erreurs système**: Services externes indisponibles

### 5. Intégration Externe
- **Service produits**: Récupération unique au démarrage
- **Service paiement**: Communication HTTP avec gestion d'erreurs
- **Résilience**: Timeout et retry implicites

### 6. Base de Données
- **ORM Peewee**: Mapping objet-relationnel propre
- **Transactions**: Opérations atomiques (paiement)
- **Relations**: ForeignKeys bien définies

### 7. Tests Complets
- **Unit tests**: Utils et services
- **Integration tests**: API complète
- **Couverture**: Tous les endpoints et cas d'erreur

## Questions Fréquentes

### Q: Pourquoi SQLite et pas PostgreSQL?
**R**: SQLite respecte les exigences du projet (base de données locale) et simplifie le déploiement pour la démonstration.

### Q: Comment gère-t-on la concurrence?
**R**: Peewee gère les transactions automatiquement. Le paiement utilise une transaction atomique pour garantir la cohérence.

### Q: Pourquoi pas de système d'authentification?
**R**: Non requis pour la première remise. Prévu pour la deuxième remise avec gestion des sessions utilisateurs.

### Q: Comment les produits sont-ils synchronisés?
**R**: Récupération unique au démarrage via `flask init-db`. Les produits sont stockés localement pour garantir la performance.

## Extension Future (Deuxième Remise)

1. **Interface HTML**: Pages web pour interagir avec l'API
2. **Authentification**: Gestion des sessions utilisateurs
3. **Historique**: Consultation des commandes passées
4. **Admin interface**: Gestion des produits et commandes
5. **Performance**: Cache distribué et optimisations

## Conclusion

Cette démonstration montre une application Flask professionnelle, robuste et prête pour la production. L'architecture propre garantit une évolution facile vers la deuxième remise.
