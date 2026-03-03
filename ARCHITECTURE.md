# Architecture INF349 - Projet de Session

## Vue d'Ensemble

Ce projet implémente une application Web Flask robuste pour la gestion de commandes Internet avec intégration de services externes. L'architecture suit les principes de Clean Architecture avec une séparation claire des responsabilités.

## Architecture Générale

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Web    │    │  Flask App      │    │ Services Externes│
│                 │◄──►│                 │◄──►│                 │
│ - HTTP/JSON     │    │ - API REST      │    │ - Produits      │
│ - Requêtes      │    │ - Validation    │    │ - Paiement      │
│ - Réponses      │    │ - Business Logic│    │ - HTTP/JSON     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Base de       │
                       │   Données       │
                       │                 │
                       │ - SQLite3       │
                       │ - Peewee ORM    │
                       │ - Transactions  │
                       └─────────────────┘
```

## Structure des Couches

### 1. Couche Présentation (routes.py)
**Responsabilité**: Gestion des requêtes HTTP et réponses

- **Validation des entrées**: JSON parsing, validation basique
- **Gestion des erreurs**: Centralisation des réponses d'erreur
- **Formatage des réponses**: Structure JSON conforme à l'API
- **Gestion des statuts HTTP**: 200, 302, 404, 422

**Principes**:
- Thin controllers: Logique minimale dans les routes
- Délégation aux services pour la logique métier
- Gestion centralisée des erreurs

### 2. Couche Métier (services.py)
**Responsabilité**: Logique métier et orchestration

- **OrderService**: Création, récupération, mise à jour des commandes
- **ProductService**: Synchronisation avec service externe
- **PaymentService**: Intégration avec service de paiement

**Principes**:
- Business logic encapsulée
- Gestion des transactions DB
- Résilience aux erreurs externes
- Validation des règles métier

### 3. Couche Accès Données (models.py)
**Responsabilité**: Persistance et mapping objet-relationnel

- **Modèles Peewee**: Product, Order, ShippingInformation, CreditCard, Transaction
- **Relations**: ForeignKeys bien définies
- **Contraintes**: Validation au niveau DB

**Principes**:
- Single Responsibility: Un modèle par entité
- Pas de logique métier dans les modèles
- Relations explicites et maintenables

### 4. Couche Utilitaire (utils.py)
**Responsabilité**: Fonctions réutilisables et calculs

- **Calculs**: Prix d'expédition, taxes par province
- **Validation**: Validation des données d'entrée
- **Formatage**: Préparation des réponses API

**Principes**:
- Pure functions: Pas d'effets de bord
- Testabilité unitaire maximale
- Réutilisabilité

### 5. Couche Erreurs (errors.py)
**Responsabilité**: Gestion centralisée des erreurs

- **Hiérarchie d'exceptions**: ValidationError, NotFoundError, BusinessError
- **Formatage uniforme**: Réponses d'erreur structurées
- **Mapping codes HTTP**: Correspondance erreur/statut

## Patterns Utilisés

### 1. Repository Pattern (via Peewee)
```python
# Accès aux données via modèles ORM
product = Product.get_by_id(product_id)
orders = Order.select().where(Order.paid == False)
```

### 2. Service Layer Pattern
```python
# Isolation de la logique métier
class OrderService:
    @staticmethod
    def create_order(product_id, quantity):
        # Validation + création + persistance
```

### 3. Dependency Injection
```python
# Injection des dépendances via app context
from . import db
from .models import Product
```

### 4. Error Handling Pattern
```python
# Gestion centralisée avec hiérarchie d'exceptions
class ValidationError(APIError):
    def __init__(self, errors, status_code=422):
```

## Flux de Données

### 1. Création de Commande
```
Client → POST /order → routes.create_order()
       ↓
OrderService.create_order()
       ↓
Product validation → DB transaction
       ↓
Order creation → Response 302 + Location
```

### 2. Processus de Paiement
```
Client → PUT /order/{id} (credit_card) → routes.update_order()
       ↓
OrderService.process_payment()
       ↓
PaymentService.process_payment() → External API
       ↓
Transaction DB update → Response 200
```

## Sécurité

### 1. Validation des Entrées
- **Type checking**: Validation des types JSON
- **Required fields**: Vérification champs obligatoires
- **Business rules**: Quantité >= 1, stock disponible

### 2. Sécurité des Données
- **Cartes de crédit**: Masquage (first/last digits uniquement)
- **Pas de passwords**: Pas d'authentification dans cette version
- **SQL Injection**: Évitée via ORM Peewee

### 3. Résilience
- **Timeouts réseaux**: Services externes
- **Rollback transactions**: Erreurs de paiement
- **Validation précoce**: Avant opérations coûteuses

## Performance

### 1. Base de Données
- **Connexions poolées**: Gestion automatique avec Peewee
- **Transactions**: Atomicité des opérations
- **Indexes**: Clés primaires et foreign keys

### 2. Cache
- **Produits locaux**: Récupération unique au démarrage
- **Pas de cache distribué**: Application single-instance

### 3. Optimisations
- **Lazy loading**: Chargement des relations uniquement si nécessaire
- **Batch operations**: Opérations en bloc quand possible

## Scalabilité

### 1. Architecture Modulaire
- **Services découplés**: Facile à étendre
- **Interfaces claires**: Contrats bien définis
- **Testabilité**: Tests unitaires isolés

### 2. Évolution Future
- **Microservices**: Extraction possible des services
- **API Gateway**: Ajout d'une couche d'abstraction
- **Message Queue**: Pour l'asynchronisme

## Déploiement

### 1. Configuration
- **Environment variables**: Séparation config/code
- **Instance folder**: Fichiers locaux (DB, logs)
- **Production config**: Override des settings par défaut

### 2. Monitoring
- **Logging**: Erreurs et opérations critiques
- **Health checks**: Endpoints de vérification
- **Metrics**: Performance et utilisation

## Tests

### 1. Stratégie de Test
- **Unit tests**: Utils et services isolés
- **Integration tests**: API complète avec DB temporaire
- **Mock services**: Services externes simulés

### 2. Couverture
- **Routes**: Tous les endpoints et codes d'erreur
- **Services**: Logique métier complète
- **Utils**: Fonctions de calcul et validation

## Conclusion

Cette architecture offre une base solide et évolutive qui respecte les principes de génie logiciel:

- **Séparation des responsabilités**: Chaque couche a un rôle clair
- **Testabilité**: Code testable à tous les niveaux
- **Maintenabilité**: Structure claire et documentée
- **Extensibilité**: Facile à faire évoluer pour la deuxième remise

Le projet est prêt pour la première remise et constitue une excellente fondation pour les fonctionnalités futures.
