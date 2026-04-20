import json
import pytest
from unittest.mock import patch, MagicMock
from inf349.models import Product, Order

def test_payment_success(client, sample_order):
    """Test successful payment processing."""
    # First update order with customer info
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
    
    # Mock successful payment service response
    mock_payment_response = {
        'success': True,
        'credit_card': {
            'name': 'John Doe',
            'first_digits': '4242',
            'last_digits': '4242',
            'expiration_year': 2024,
            'expiration_month': 9
        },
        'transaction': {
            'id': 'test_transaction_id',
            'success': True,
            'amount_charged': 2875  # 2000 + 500 + 15% tax = 2875
        }
    }
    
    with patch('inf349.services.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_payment_response
        
        payment_data = {
            "credit_card": {
                "name": "John Doe",
                "number": "4242 4242 4242 4242",
                "expiration_year": 2024,
                "expiration_month": 9,
                "cvv": "123"
            }
        }
        
        response = client.put(f'/order/{sample_order.id}',
                             data=json.dumps(payment_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        order = data['order']
        
        assert order['paid'] == True
        assert order['credit_card']['name'] == 'John Doe'
        assert order['credit_card']['first_digits'] == '4242'
        assert order['credit_card']['last_digits'] == '4242'
        assert order['transaction']['id'] == 'test_transaction_id'
        assert order['transaction']['success'] == True

def test_payment_without_customer_info(client, sample_order):
    """Test payment without customer information."""
    payment_data = {
        "credit_card": {
            "name": "John Doe",
            "number": "4242 4242 4242 4242",
            "expiration_year": 2024,
            "expiration_month": 9,
            "cvv": "123"
        }
    }
    
    response = client.put(f'/order/{sample_order.id}',
                         data=json.dumps(payment_data),
                         content_type='application/json')
    
    assert response.status_code == 422
    
    data = json.loads(response.data)
    assert 'errors' in data
    assert 'order' in data['errors']
    assert data['errors']['order']['code'] == 'missing-fields'
    assert 'client' in data['errors']['order']['name']

def test_payment_already_paid(client, sample_order):
    """Test payment on already paid order."""
    # First update with customer info
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
    
    # Mock successful payment and mark as paid
    mock_payment_response = {
        'success': True,
        'credit_card': {
            'name': 'John Doe',
            'first_digits': '4242',
            'last_digits': '4242',
            'expiration_year': 2024,
            'expiration_month': 9
        },
        'transaction': {
            'id': 'test_transaction_id',
            'success': True,
            'amount_charged': 2875
        }
    }
    
    with patch('inf349.services.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_payment_response
        
        payment_data = {
            "credit_card": {
                "name": "John Doe",
                "number": "4242 4242 4242 4242",
                "expiration_year": 2024,
                "expiration_month": 9,
                "cvv": "123"
            }
        }
        
        # First payment
        response = client.put(f'/order/{sample_order.id}',
                             data=json.dumps(payment_data),
                             content_type='application/json')
        assert response.status_code == 200
        
        # Second payment attempt
        response = client.put(f'/order/{sample_order.id}',
                             data=json.dumps(payment_data),
                             content_type='application/json')
        
        assert response.status_code == 422
        
        data = json.loads(response.data)
        assert 'errors' in data
        assert 'order' in data['errors']
        assert data['errors']['order']['code'] == 'already-paid'

def test_payment_card_declined(client, sample_order):
    """Test payment with declined card."""
    # First update with customer info
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
    
    # Mock declined payment response
    mock_payment_response = {
        'errors': {
            'credit_card': {
                'code': 'card-declined',
                'name': 'La carte de crédit a été déclinée'
            }
        }
    }
    
    with patch('inf349.services.requests.post') as mock_post:
        mock_post.return_value.status_code = 422
        mock_post.return_value.json.return_value = mock_payment_response
        
        payment_data = {
            "credit_card": {
                "name": "John Doe",
                "number": "4000 0000 0000 0002",  # Declined card
                "expiration_year": 2024,
                "expiration_month": 9,
                "cvv": "123"
            }
        }
        
        response = client.put(f'/order/{sample_order.id}',
                             data=json.dumps(payment_data),
                             content_type='application/json')
        
        assert response.status_code == 422
        
        data = json.loads(response.data)
        assert 'errors' in data
        assert 'credit_card' in data['errors']
        assert data['errors']['credit_card']['code'] == 'card-declined'

def test_payment_missing_fields(client, sample_order):
    """Test payment with missing credit card fields."""
    # First update with customer info
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
    
    # Payment data missing CVV
    payment_data = {
        "credit_card": {
            "name": "John Doe",
            "number": "4242 4242 4242 4242",
            "expiration_year": 2024,
            "expiration_month": 9
            # Missing cvv
        }
    }
    
    response = client.put(f'/order/{sample_order.id}',
                         data=json.dumps(payment_data),
                         content_type='application/json')
    
    assert response.status_code == 422
    
    data = json.loads(response.data)
    assert 'errors' in data
    assert 'credit_card' in data['errors']

def test_payment_service_error(client, sample_order):
    """Test payment when service is unavailable."""
    # First update with customer info
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
    
    # Mock service error
    with patch('inf349.services.requests.post') as mock_post:
        mock_post.side_effect = Exception("Service unavailable")
        
        payment_data = {
            "credit_card": {
                "name": "John Doe",
                "number": "4242 4242 4242 4242",
                "expiration_year": 2024,
                "expiration_month": 9,
                "cvv": "123"
            }
        }
        
        response = client.put(f'/order/{sample_order.id}',
                             data=json.dumps(payment_data),
                             content_type='application/json')
        
        assert response.status_code == 422
        
        data = json.loads(response.data)
        assert 'errors' in data
        assert 'credit_card' in data['errors']

def test_tax_calculation_by_province(client):
    """Test tax calculation for different provinces."""
    # Create order for each province and verify tax calculation
    provinces_tax = {
        'QC': 0.15,
        'ON': 0.13,
        'AB': 0.05,
        'BC': 0.12,
        'NS': 0.14
    }
    
    for province, expected_rate in provinces_tax.items():
        # Create order
        order_data = {
            "product": {
                "id": 1,
                "quantity": 1
            }
        }
        
        response = client.post('/order', 
                              data=json.dumps(order_data),
                              content_type='application/json')
        
        assert response.status_code == 302
        location = response.headers['Location']
        order_id = location.split('/')[-1]
        
        # Update with customer info in specific province
        update_data = {
            "order": {
                "email": f"test@{province.lower()}.com",
                "shipping_information": {
                    "country": "Canada",
                    "address": "123 Test St",
                    "postal_code": "G7X 3Y7",
                    "city": "Test City",
                    "province": province
                }
            }
        }
        
        response = client.put(f'/order/{order_id}',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        order = data['order']
        
        # Verify tax calculation (tax applies only to total_price, not shipping)
        expected_total = order['total_price'] * (1 + expected_rate)

        assert abs(order['total_price_tax'] - expected_total) < 1
