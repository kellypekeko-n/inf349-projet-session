# 🛍️ INF349 - Projet de Session Flask

## 📋 Description

Application Flask complète pour la gestion de commandes Internet avec intégration de paiement. Implémente une API REST robuste avec base de données SQLite et ORM Peewee.

## ✅ Fonctionnalités

### 🌐 API REST Complète
- **GET /** : Liste de tous les produits (incluant hors stock)
- **POST /order** : Création de commande (302 + Location)
- **GET /order/<id>** : Consultation de commande avec calculs automatiques
- **PUT /order/<id>** : Mise à jour client ET paiement séparés

### 💰 Calculs Automatiques
- **Frais d'expédition** : 5$ (≤500g), 10$ (500g-2kg), 25$ (≥2kg)
- **Taxes provinciales** : QC 15%, ON 13%, AB 5%, BC 12%, NS 14%
- **Prix totaux** : Calcul automatique avec taxes

### 🗄️ Base de Données
- **ORM Peewee** : Models Product, Order, ShippingInformation, CreditCard, Transaction
- **SQLite3** : Base de données locale
- **Relations** : ForeignKeys bien définies

### 🌍 Services Externes
- **Produits** : http://dimensweb.uqac.ca/~jgnault/shops/products/
- **Paiement** : http://dimensweb.uqac.ca/~jgnault/shops/pay/
- **Récupération unique** au démarrage + cache local

### 🧪 Tests Complets
- **Tests unitaires** : Utils, services, validation
- **Tests d'intégration** : API complète
- **Tests d'erreurs** : Tous les cas d'erreur

## 🚀 Installation et Démarrage

### 1️⃣ Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2️⃣ Initialisation de la base de données
```bash
python -c "from inf349 import create_app; app = create_app(); app.app_context().push(); from inf349.models import initialize_db; from inf349 import db; initialize_db(db); print('Base de données initialisée')"
```

### 3️⃣ Démarrage de l'application
```bash
python start_app.py
```

**L'application sera accessible sur : http://localhost:5000**

---

## 🧪 Tests Automatisés

### Lancer tous les tests
```bash
python run_tests.py
```

**Résultat attendu :**
```
Running INF349 Project Tests
====================================
✅ All tests passed!
```

### Tests manuels avec curl
```bash
# 1. Obtenir les produits
curl -X GET http://localhost:5000/

# 2. Créer une commande
curl -X POST http://localhost:5000/order \
  -H "Content-Type: application/json" \
  -d '{"product": {"id": 1, "quantity": 2}}'

# 3. Consulter une commande
curl -X GET http://localhost:5000/order/1

# 4. Mettre à jour les infos client
curl -X PUT http://localhost:5000/order/1 \
  -H "Content-Type: application/json" \
  -d '{
    "order": {
      "email": "test@example.com",
      "shipping_information": {
        "country": "Canada",
        "address": "123 Test St",
        "postal_code": "G7X 3Y7",
        "city": "Chicoutimi",
        "province": "QC"
      }
    }
  }'
```

---

## 📁 Structure du Projet

```
inf349/
├── __init__.py          # Initialisation Flask
├── models.py            # Base de données Peewee
├── routes.py            # API REST
├── services.py          # Logique métier
├── utils.py             # Calculs et validation
├── errors.py            # Gestion d'erreurs
├── commands.py          # Commandes Flask
└── tests/               # Tests complets
    ├── conftest.py      # Configuration tests
    ├── test_products.py # Tests produits
    ├── test_orders.py   # Tests commandes
    ├── test_payment.py  # Tests paiements
    └── test_utils.py    # Tests utilitaires

Fichiers racine:
├── requirements.txt     # Dépendances Python
├── start_app.py       # Lanceur application
├── run_tests.py       # Tests automatisés
└── README.md          # Documentation
```

---

## 🎯 Cas d'Utilisation

### Scénario 1 : Commande Simple
1. Client consulte les produits disponibles
2. Client crée une commande avec produit et quantité
3. Système calcule automatiquement : prix total + frais d'expédition + taxes
4. Client reçoit une confirmation avec ID de commande

### Scénario 2 : Commande Complète
1. Client ajoute ses informations (email, adresse)
2. Système recalcule les taxes selon la province
3. Client procède au paiement avec carte de crédit
4. Système communique avec service externe de paiement
5. Transaction enregistrée et commande marquée comme payée

---

## 🛡️ Gestion d'Erreurs

### Codes d'erreur HTTP
- **200** : Succès (GET/PUT réussis)
- **302** : Redirection (POST /order réussi)
- **404** : Ressource non trouvée (GET /order/<id>)
- **422** : Erreur de validation (champs manquants, hors stock, etc.)

### Messages d'erreur
- **missing-fields** : Champs obligatoires manquants
- **out-of-inventory** : Produit non disponible
- **already-paid** : Commande déjà payée
- **card-declined** : Carte de crédit refusée

---

## 🔧 Dépannage

### Problème : Port déjà utilisé
```bash
# Changer de port dans start_app.py
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Problème : Base de données corrompue
```bash
# Supprimer et recréer
rm inf349/instance/database.db
python start_app.py
```

### Problème : Services externes indisponibles
L'application utilise un cache local des produits, donc fonctionne même si les services externes sont indisponibles.

---

## 🌍 Déploiement sur GitHub

### 1. Initialiser Git
```bash
git init
git add .
git commit -m "Initial commit: INF349 Flask E-commerce API"
```

### 2. Créer dépôt GitHub
1. Allez sur https://github.com
2. Cliquez sur "New repository"
3. Nom : `inf349-projet-session`
4. Description : `INF349 - Projet de Session Flask E-commerce API`
5. Public (pour la remise)
6. NE PAS cocher "Add README"

### 3. Connecter et pousser
```bash
# Remplacez VOTRE_USERNAME par votre vrai nom d'utilisateur
git remote add origin https://github.com/VOTRE_USERNAME/inf349-projet-session.git
git push -u origin main
```

---

## 🎓 Pour la Remise Universitaire

### ✅ Checklist de Validation
- [ ] Application démarre sans erreur
- [ ] Tous les tests passent (`python run_tests.py`)
- [ ] API REST fonctionne (tests curl)
- [ ] Calculs automatiques corrects
- [ ] Gestion d'erreurs robuste
- [ ] Base de données fonctionnelle
- [ ] Documentation complète

### 📊 Points Clés à Démontrer
1. **API REST professionnelle** avec codes HTTP standards
2. **Calculs métier** automatiques et précis
3. **Architecture propre** avec séparation des responsabilités
4. **Tests complets** avec couverture maximale
5. **Gestion d'erreurs** centralisée et structurée
6. **Services externes** intégrés avec résilience
7. **Documentation** professionnelle et complète

---

## 🏆 Architecture Technique

### Clean Architecture
- **routes.py** : API REST uniquement
- **services.py** : Logique métier isolée
- **models.py** : Accès données via ORM
- **utils.py** : Fonctions pures réutilisables
- **errors.py** : Gestion centralisée des erreurs

### Patterns Utilisés
- **Service Layer** : Isolation de la logique métier
- **Repository Pattern** : Via ORM Peewee
- **Error Handling** : Hiérarchie d'exceptions
- **Dependency Injection** : Via Flask app context

---

## 📞 Support et Développement

### Technologies
- **Python 3.12** : Compatible avec spécifications
- **Flask 2.3.3** : Framework web léger et puissant
- **Peewee 3.16.2** : ORM simple et efficace
- **SQLite3** : Base de données locale et fiable
- **Requests** : Communication avec services externes

### Standards Respectés
- **PEP8** : Style Python professionnel
- **REST** : API respectant les standards HTTP
- **JSON** : Format d'échange standard
- **SQL** : Base de données relationnelle

---

## 🎯 Conclusion

Ce projet INF349 représente une **solution professionnelle et complète** pour la gestion de commandes en ligne. Il démontre :

- ✅ **Maîtrise technique** de Flask et écosystème Python
- ✅ **Architecture logicielle** moderne et maintenable
- ✅ **Qualité de code** industrielle et testée
- ✅ **Rigueur de développement** avec gestion d'erreurs
- ✅ **Documentation** professionnelle et complète

**Prêt pour la remise universitaire et pour l'évolution future !** 🚀

---

*Développé avec Python 3.12, Flask 2.3.3, Peewee 3.16.2*
