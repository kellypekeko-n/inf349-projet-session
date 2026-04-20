import pytest
from decimal import Decimal
from inf349.utils import (
    calculate_shipping_price, 
    calculate_tax, 
    validate_order_creation,
    validate_order_update,
    validate_payment_data,
    format_order_response
)

def test_calculate_shipping_price():
    """Test shipping price calculation."""
    # Test <= 500g
    assert calculate_shipping_price(400) == 500  # $5.00
    assert calculate_shipping_price(500) == 500  # $5.00
    
    # Test 500g - 2kg
    assert calculate_shipping_price(501) == 1000  # $10.00
    assert calculate_shipping_price(1500) == 1000  # $10.00
    assert calculate_shipping_price(2000) == 2500  # >= 2000g → $25.00
    
    # Test > 2kg
    assert calculate_shipping_price(2001) == 2500  # $25.00
    assert calculate_shipping_price(3000) == 2500  # $25.00

def test_calculate_tax():
    """Test tax calculation for different provinces."""
    # Test QC (15%)
    tax = calculate_tax(10000, 'QC')  # $100.00
    assert tax == Decimal('1500.00')  # 15% of $100.00
    
    # Test ON (13%)
    tax = calculate_tax(10000, 'ON')  # $100.00
    assert tax == Decimal('1300.00')  # 13% of $100.00
    
    # Test AB (5%)
    tax = calculate_tax(10000, 'AB')  # $100.00
    assert tax == Decimal('500.00')   # 5% of $100.00
    
    # Test BC (12%)
    tax = calculate_tax(10000, 'BC')  # $100.00
    assert tax == Decimal('1200.00')  # 12% of $100.00
    
    # Test NS (14%)
    tax = calculate_tax(10000, 'NS')  # $100.00
    assert tax == Decimal('1400.00')  # 14% of $100.00
    
    # Test unknown province (returns 0)
    tax = calculate_tax(10000, 'XX')  # $100.00
    assert tax == Decimal('0.00')  # unknown province → no tax

def test_validate_order_creation():
    """Test order creation validation."""
    # Valid data
    valid_data = {
        "product": {
            "id": 1,
            "quantity": 2
        }
    }
    errors = validate_order_creation(valid_data)
    assert len(errors) == 0
    
    # Missing product
    invalid_data = {}
    errors = validate_order_creation(invalid_data)
    assert len(errors) == 1
    assert errors[0]['field'] == 'product'
    assert errors[0]['code'] == 'missing-fields'
    
    # Missing product fields
    invalid_data = {
        "product": {
            "id": 1
            # Missing quantity
        }
    }
    errors = validate_order_creation(invalid_data)
    assert len(errors) == 1
    assert errors[0]['field'] == 'product'
    assert errors[0]['code'] == 'missing-fields'
    
    # Invalid quantity
    invalid_data = {
        "product": {
            "id": 1,
            "quantity": 0
        }
    }
    errors = validate_order_creation(invalid_data)
    assert len(errors) == 1
    assert errors[0]['field'] == 'product'
    assert errors[0]['code'] == 'missing-fields'
    
    # Product not a dict
    invalid_data = {
        "product": "invalid"
    }
    errors = validate_order_creation(invalid_data)
    assert len(errors) == 1
    assert errors[0]['field'] == 'product'
    assert errors[0]['code'] == 'missing-fields'

def test_validate_order_update():
    """Test order update validation."""
    # Valid data
    valid_data = {
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
    }
    errors = validate_order_update(valid_data)
    assert len(errors) == 0
    
    # Missing order
    invalid_data = {}
    errors = validate_order_update(invalid_data)
    assert len(errors) == 1
    assert errors[0]['field'] == 'order'
    assert errors[0]['code'] == 'missing-fields'
    
    # Missing email
    invalid_data = {
        "order": {
            "shipping_information": {
                "country": "Canada",
                "address": "123 Test St",
                "postal_code": "G7X 3Y7",
                "city": "Chicoutimi",
                "province": "QC"
            }
        }
    }
    errors = validate_order_update(invalid_data)
    assert len(errors) == 1
    assert errors[0]['field'] == 'order'
    assert errors[0]['code'] == 'missing-fields'
    
    # Missing shipping info fields
    invalid_data = {
        "order": {
            "email": "test@example.com",
            "shipping_information": {
                "country": "Canada",
                "address": "123 Test St"
                # Missing postal_code, city, province
            }
        }
    }
    errors = validate_order_update(invalid_data)
    assert len(errors) == 1
    assert errors[0]['field'] == 'order'
    assert errors[0]['code'] == 'missing-fields'

def test_validate_payment_data():
    """Test payment data validation."""
    # Valid data
    valid_data = {
        "credit_card": {
            "name": "John Doe",
            "number": "4242 4242 4242 4242",
            "expiration_year": 2024,
            "expiration_month": 9,
            "cvv": "123"
        }
    }
    errors = validate_payment_data(valid_data)
    assert len(errors) == 0
    
    # Missing credit_card
    invalid_data = {}
    errors = validate_payment_data(invalid_data)
    assert len(errors) == 1
    assert errors[0]['field'] == 'credit_card'
    assert errors[0]['code'] == 'missing-fields'
    
    # Missing credit card fields
    invalid_data = {
        "credit_card": {
            "name": "John Doe",
            "number": "4242 4242 4242 4242",
            "expiration_year": 2024,
            "expiration_month": 9
            # Missing cvv
        }
    }
    errors = validate_payment_data(invalid_data)
    assert len(errors) == 1
    assert errors[0]['field'] == 'credit_card'
    assert errors[0]['code'] == 'missing-fields'

def test_format_order_response():
    """Test order response formatting."""
    from inf349.models import Product, Order, ShippingInformation, CreditCard, Transaction
    from decimal import Decimal
    
    # Create mock order (this would normally be done in a test fixture)
    # For this test, we'll create a simple mock object
    class MockItem:
        def __init__(self):
            self.product_id = 1
            self.quantity = 2

    class MockOrder:
        def __init__(self):
            self.id = 1
            self.total_price = 2000
            self.total_price_tax = Decimal('2300.00')
            self.email = 'test@example.com'
            self.paid = True
            self.shipping_price = 500
            self.items = [MockItem()]

            # Mock related objects
            self.shipping_information = MockShipping()
            self.credit_card = MockCreditCard()
            self.transaction = MockTransaction()

    class MockShipping:
        def __init__(self):
            self.country = 'Canada'
            self.address = '123 Test St'
            self.postal_code = 'G7X 3Y7'
            self.city = 'Chicoutimi'
            self.province = 'QC'

    class MockCreditCard:
        def __init__(self):
            self.name = 'John Doe'
            self.first_digits = '4242'
            self.last_digits = '4242'
            self.expiration_year = 2024
            self.expiration_month = 9

    class MockTransaction:
        def __init__(self):
            self.id = 'test_tx_id'
            self.success = True
            self.amount_charged = 2300
            self.error_code = None
            self.error_name = None
    
    order = MockOrder()
    response = format_order_response(order)
    
    assert 'order' in response
    order_data = response['order']
    
    assert order_data['id'] == 1
    assert order_data['total_price'] == 2000
    assert order_data['total_price_tax'] == 2300.00
    assert order_data['email'] == 'test@example.com'
    assert order_data['paid'] == True
    assert order_data['shipping_price'] == 500
    
    # Check product info
    assert order_data['products'][0]['id'] == 1
    assert order_data['products'][0]['quantity'] == 2
    
    # Check shipping info
    shipping = order_data['shipping_information']
    assert shipping['country'] == 'Canada'
    assert shipping['address'] == '123 Test St'
    assert shipping['postal_code'] == 'G7X 3Y7'
    assert shipping['city'] == 'Chicoutimi'
    assert shipping['province'] == 'QC'
    
    # Check credit card info
    credit_card = order_data['credit_card']
    assert credit_card['name'] == 'John Doe'
    assert credit_card['first_digits'] == '4242'
    assert credit_card['last_digits'] == '4242'
    assert credit_card['expiration_year'] == 2024
    assert credit_card['expiration_month'] == 9
    
    # Check transaction info
    transaction = order_data['transaction']
    assert transaction['id'] == 'test_tx_id'
    assert transaction['success'] == True
    assert transaction['amount_charged'] == 2300
