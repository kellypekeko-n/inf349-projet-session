import json
from inf349.models import Product, Order

def test_create_order_success(client):
    """Test successful order creation."""
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
    assert 'Location' in response.headers
    
    # Check that order was created
    location = response.headers['Location']
    order_id = location.split('/')[-1]
    
    # Get the order
    response = client.get(f'/order/{order_id}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    order = data['order']
    
    assert order['product']['id'] == 1
    assert order['product']['quantity'] == 2
    assert order['total_price'] == 2000  # 2 * $10.00
    assert order['shipping_price'] == 500  # Weight: 2 * 200g = 400g <= 500g
    assert order['paid'] == False
    assert order['email'] is None
    assert order['credit_card'] == {}
    assert order['transaction'] == {}

def test_create_order_missing_product(client):
    """Test order creation with missing product."""
    order_data = {}
    
    response = client.post('/order', 
                          data=json.dumps(order_data),
                          content_type='application/json')
    
    assert response.status_code == 422
    
    data = json.loads(response.data)
    assert 'errors' in data
    assert 'product' in data['errors']
    assert data['errors']['product']['code'] == 'missing-fields'

def test_create_order_missing_fields(client):
    """Test order creation with missing product fields."""
    order_data = {
        "product": {
            "id": 1
            # Missing quantity
        }
    }
    
    response = client.post('/order', 
                          data=json.dumps(order_data),
                          content_type='application/json')
    
    assert response.status_code == 422
    
    data = json.loads(response.data)
    assert 'errors' in data
    assert 'product' in data['errors']
    assert data['errors']['product']['code'] == 'missing-fields'

def test_create_order_invalid_quantity(client):
    """Test order creation with invalid quantity."""
    order_data = {
        "product": {
            "id": 1,
            "quantity": 0
        }
    }
    
    response = client.post('/order', 
                          data=json.dumps(order_data),
                          content_type='application/json')
    
    assert response.status_code == 422
    
    data = json.loads(response.data)
    assert 'errors' in data
    assert 'product' in data['errors']
    assert data['errors']['product']['code'] == 'missing-fields'

def test_create_order_out_of_inventory(client):
    """Test order creation with out of stock product."""
    order_data = {
        "product": {
            "id": 2,  # This product is out of stock
            "quantity": 1
        }
    }
    
    response = client.post('/order', 
                          data=json.dumps(order_data),
                          content_type='application/json')
    
    assert response.status_code == 422
    
    data = json.loads(response.data)
    assert 'errors' in data
    assert 'product' in data['errors']
    assert data['errors']['product']['code'] == 'out-of-inventory'

def test_create_order_nonexistent_product(client):
    """Test order creation with non-existent product."""
    order_data = {
        "product": {
            "id": 999,  # Non-existent product
            "quantity": 1
        }
    }
    
    response = client.post('/order', 
                          data=json.dumps(order_data),
                          content_type='application/json')
    
    assert response.status_code == 422
    
    data = json.loads(response.data)
    assert 'errors' in data
    assert 'product' in data['errors']
    assert data['errors']['product']['code'] == 'missing-fields'

def test_get_order_not_found(client):
    """Test getting non-existent order."""
    response = client.get('/order/999')
    assert response.status_code == 404

def test_get_order_success(client, sample_order):
    """Test getting existing order."""
    response = client.get(f'/order/{sample_order.id}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'order' in data
    
    order = data['order']
    assert order['id'] == sample_order.id
    assert order['product']['id'] == 1
    assert order['product']['quantity'] == 2
    assert order['total_price'] == 2000
    assert order['shipping_price'] == 500
    assert order['paid'] == False

def test_update_order_customer_info_success(client, sample_order):
    """Test successful customer information update."""
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
    
    response = client.put(f'/order/{sample_order.id}',
                         data=json.dumps(update_data),
                         content_type='application/json')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    order = data['order']
    
    assert order['email'] == "test@example.com"
    assert order['shipping_information']['country'] == "Canada"
    assert order['shipping_information']['address'] == "123 Test St"
    assert order['shipping_information']['postal_code'] == "G7X 3Y7"
    assert order['shipping_information']['city'] == "Chicoutimi"
    assert order['shipping_information']['province'] == "QC"
    
    # Check tax calculation (QC = 15%)
    expected_total = 2000 + 500  # total_price + shipping_price
    expected_tax = expected_total * 0.15
    assert abs(order['total_price_tax'] - (expected_total + expected_tax)) < 0.01

def test_update_order_missing_fields(client, sample_order):
    """Test order update with missing required fields."""
    update_data = {
        "order": {
            "email": "test@example.com",
            "shipping_information": {
                "country": "Canada",
                "address": "123 Test St"
                # Missing postal_code, city, province
            }
        }
    }
    
    response = client.put(f'/order/{sample_order.id}',
                         data=json.dumps(update_data),
                         content_type='application/json')
    
    assert response.status_code == 422
    
    data = json.loads(response.data)
    assert 'errors' in data
    assert 'order' in data['errors']
    assert data['errors']['order']['code'] == 'missing-fields'

def test_update_order_not_found(client):
    """Test updating non-existent order."""
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
    
    response = client.put('/order/999',
                         data=json.dumps(update_data),
                         content_type='application/json')
    
    assert response.status_code == 404

def test_shipping_price_calculation(client):
    """Test shipping price calculation for different weights."""
    # Light product (<= 500g)
    order_data = {
        "product": {
            "id": 1,  # 200g each
            "quantity": 2  # Total: 400g
        }
    }
    
    response = client.post('/order', 
                          data=json.dumps(order_data),
                          content_type='application/json')
    
    assert response.status_code == 302
    location = response.headers['Location']
    order_id = location.split('/')[-1]
    
    response = client.get(f'/order/{order_id}')
    data = json.loads(response.data)
    assert data['order']['shipping_price'] == 500  # $5.00
    
    # Heavy product (> 2kg)
    order_data = {
        "product": {
            "id": 3,  # 3000g each
            "quantity": 1  # Total: 3000g
        }
    }
    
    response = client.post('/order', 
                          data=json.dumps(order_data),
                          content_type='application/json')
    
    assert response.status_code == 302
    location = response.headers['Location']
    order_id = location.split('/')[-1]
    
    response = client.get(f'/order/{order_id}')
    data = json.loads(response.data)
    assert data['order']['shipping_price'] == 2500  # $25.00
