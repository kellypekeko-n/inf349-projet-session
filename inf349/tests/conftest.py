import os
import pytest
from inf349 import create_app
from inf349.models import (
    db, Product, Order, OrderItem,
    ShippingInformation, CreditCard, Transaction, User,
)
from inf349.services import OrderService

# ── Données de test alignées sur test_functional.py ────────────────────────────
# id=1 : prix=2810 cts, poids=400g, en stock   → 2×400g = 800g → shipping 1000
# id=2 : prix=2945 cts, poids=200g, en stock   → multi-produit
# id=3 : prix=5000 cts, poids=3000g, en stock  → shipping lourd 2500
# id=4 : hors stock                             → test out-of-inventory
TEST_PRODUCTS = [
    {"id": 1, "name": "Produit Test 1",  "description": "Desc 1",  "price": 2810,
     "in_stock": True,  "weight": 400,  "image": "p1.jpg"},
    {"id": 2, "name": "Produit Test 2",  "description": "Desc 2",  "price": 2945,
     "in_stock": True,  "weight": 200,  "image": "p2.jpg"},
    {"id": 3, "name": "Produit Lourd",   "description": "Lourd",   "price": 5000,
     "in_stock": True,  "weight": 3000, "image": "p3.jpg"},
    {"id": 4, "name": "Produit Épuisé",  "description": "Épuisé",  "price": 1500,
     "in_stock": False, "weight": 200,  "image": "p4.jpg"},
]


@pytest.fixture
def app():
    """App Flask en mode TESTING, connectée à la base PostgreSQL."""
    test_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "PAYMENT_SERVICE_URL": "https://dimensweb.uqac.ca/~jgnault/shops/pay/",
        "PRODUCT_SERVICE_URL": "https://dimensweb.uqac.ca/~jgnault/shops/products/",
    })

    if db.deferred:
        db.init(
            os.environ.get("DB_NAME", "api8inf349"),
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "user"),
            password=os.environ.get("DB_PASSWORD", "pass"),
            port=int(os.environ.get("DB_PORT", 5432)),
        )

    if db.is_closed():
        db.connect()

    db.drop_tables(
        [OrderItem, Order, ShippingInformation, CreditCard, Transaction, User, Product],
        safe=True,
    )
    db.create_tables(
        [Product, ShippingInformation, CreditCard, Transaction, Order, OrderItem, User],
        safe=True,
    )

    for p in TEST_PRODUCTS:
        Product.create(**p)

    if not db.is_closed():
        db.close()

    yield test_app

    if db.is_closed():
        db.connect()
    db.drop_tables(
        [OrderItem, Order, ShippingInformation, CreditCard, Transaction, User, Product],
        safe=True,
    )
    if not db.is_closed():
        db.close()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def sample_order(app):
    """Commande de test : 2 × produit id=1 (total 5620 cts, shipping 1000 cts)."""
    with app.test_request_context():
        if db.is_closed():
            db.connect()
        order = OrderService.create_order([{"id": 1, "quantity": 2}])
        if not db.is_closed():
            db.close()
        return order
