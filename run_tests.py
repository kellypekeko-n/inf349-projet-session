#!/usr/bin/env python3
"""
Simple test runner without pytest dependency issues
"""
import sys
import os
import tempfile
import json
from decimal import Decimal

# Add project root to path
sys.path.insert(0, '.')

from inf349 import create_app
from inf349.models import initialize_db, Product, Order
from inf349 import db
from inf349.utils import calculate_shipping_price, calculate_tax, validate_order_creation

def test_utils():
    """Test utility functions"""
    print("=== Testing Utils ===")
    
    # Test shipping price calculation
    assert calculate_shipping_price(400) == 500  # <= 500g
    assert calculate_shipping_price(1500) == 1000  # 500g-2kg
    assert calculate_shipping_price(3000) == 2500  # > 2kg
    print("✓ Shipping price calculation")
    
    # Test tax calculation
    tax = calculate_tax(10000, 'QC')  # $100.00
    assert tax == Decimal('1500.00')  # 15%
    tax = calculate_tax(10000, 'ON')  # $100.00
    assert tax == Decimal('1300.00')  # 13%
    print("✓ Tax calculation")
    
    # Test validation
    valid_data = {"product": {"id": 1, "quantity": 2}}
    errors = validate_order_creation(valid_data)
    assert len(errors) == 0
    print("✓ Valid order validation")
    
    invalid_data = {"product": {"id": 1}}  # Missing quantity
    errors = validate_order_creation(invalid_data)
    assert len(errors) > 0
    print("✓ Invalid order validation")

def test_api():
    """Test API endpoints"""
    print("\n=== Testing API ===")
    
    # Create test app
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
        'PRODUCT_SERVICE_URL': 'http://dimensweb.uqac.ca/~jgnault/shops/products/',
        'PAYMENT_SERVICE_URL': 'http://dimensweb.uqac.ca/~jgnault/shops/pay/'
    })
    
    with app.app_context():
        initialize_db(db)
        
        # Fetch products
        from inf349.services import ProductService
        product_service = ProductService(app.config['PRODUCT_SERVICE_URL'])
        products = product_service.fetch_products()
        print(f"✓ Fetched {len(products)} products")
        
        with app.test_client() as client:
            # Test GET /
            response = client.get('/')
            assert response.status_code == 200
            data = response.get_json()
            assert 'products' in data
            assert len(data['products']) > 0
            print("✓ GET / products")
            
            # Test POST /order (valid)
            order_data = {
                "product": {
                    "id": 1,
                    "quantity": 2
                }
            }
            
            response = client.post('/order', 
                                  data=json.dumps(order_data), 
                                  content_type='application/json')
            assert response.status_code == 302
            location = response.headers.get('Location')
            assert location is not None
            order_id = int(location.split('/')[-1])
            print(f"✓ POST /order created order {order_id}")
            
            # Test GET /order/<id>
            response = client.get(f'/order/{order_id}')
            assert response.status_code == 200
            order = response.get_json()['order']
            assert order['id'] == order_id
            assert order['product']['id'] == 1
            assert order['product']['quantity'] == 2
            assert order['paid'] == False
            print("✓ GET /order/<id>")
            
            # Test PUT /order/<id> (customer info)
            update_data = {
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
            
            response = client.put(f'/order/{order_id}',
                                 data=json.dumps(update_data),
                                 content_type='application/json')
            assert response.status_code == 200
            order = response.get_json()['order']
            assert order['email'] == "test@example.com"
            assert order['shipping_information']['province'] == "QC"
            print("✓ PUT /order/<id> customer info")
            
            # Test POST /order (invalid - missing fields)
            invalid_order = {"product": {"id": 1}}  # Missing quantity
            response = client.post('/order', 
                                  data=json.dumps(invalid_order), 
                                  content_type='application/json')
            assert response.status_code == 422
            errors = response.get_json()
            assert 'errors' in errors
            print("✓ POST /order validation error")
            
            # Test GET /order/999 (not found)
            response = client.get('/order/999')
            assert response.status_code == 404
            print("✓ GET /order/<id> not found")
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

def main():
    """Run all tests"""
    print("Running INF349 Project Tests")
    print("=" * 50)
    
    try:
        test_utils()
        test_api()
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
