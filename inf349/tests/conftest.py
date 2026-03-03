import pytest
import tempfile
import os
from inf349 import create_app
from inf349.models import Product, Order, ShippingInformation, CreditCard, Transaction, initialize_db
from inf349 import db

@pytest.fixture
def app():
    """Create and configure a test app."""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
        'PRODUCT_SERVICE_URL': 'http://dimensweb.uqac.ca/~jgnault/shops/products/',
        'PAYMENT_SERVICE_URL': 'http://dimensweb.uqac.ca/~jgnault/shops/pay/'
    })
    
    with app.app_context():
        initialize_db(db)
        
        # Create test products
        Product.create(
            id=1,
            name="Test Product 1",
            description="Test description 1",
            price=1000,  # $10.00 in cents
            in_stock=True,
            weight=200,
            image="test1.jpg"
        )
        
        Product.create(
            id=2,
            name="Test Product 2",
            description="Test description 2",
            price=2000,  # $20.00 in cents
            in_stock=False,
            weight=500,
            image="test2.jpg"
        )
        
        Product.create(
            id=3,
            name="Heavy Product",
            description="Heavy product for shipping tests",
            price=5000,  # $50.00 in cents
            in_stock=True,
            weight=3000,
            image="heavy.jpg"
        )
    
    yield app
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's CLI commands."""
    return app.test_cli_runner()

@pytest.fixture
def sample_order(app):
    """Create a sample order for testing."""
    with app.app_context():
        product = Product.get_by_id(1)
        order = Order.create(
            product=product,
            quantity=2,
            total_price=2000,  # 2 * $10.00
            shipping_price=500  # $5.00 for weight <= 500g
        )
        return order
