import json
from inf349.models import Product

def test_get_products(client):
    """Test getting all products."""
    response = client.get('/')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'products' in data
    assert len(data['products']) == 3  # We created 3 test products
    
    # Check product structure
    product = data['products'][0]
    assert 'id' in product
    assert 'name' in product
    assert 'description' in product
    assert 'price' in product
    assert 'in_stock' in product
    assert 'weight' in product
    assert 'image' in product
    
    # Check price is in dollars (not cents)
    assert product['price'] == 10.0  # $10.00 from our test data

def test_get_products_includes_out_of_stock(client):
    """Test that out of stock products are included in the list."""
    response = client.get('/')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    products = data['products']
    
    # Should include both in-stock and out-of-stock products
    in_stock_products = [p for p in products if p['in_stock']]
    out_of_stock_products = [p for p in products if not p['in_stock']]
    
    assert len(in_stock_products) == 2
    assert len(out_of_stock_products) == 1
    
    # Check the out of stock product
    out_of_stock = out_of_stock_products[0]
    assert out_of_stock['id'] == 2
    assert out_of_stock['name'] == "Test Product 2"
    assert out_of_stock['in_stock'] == False

def test_product_data_integrity(client):
    """Test that product data is correctly formatted."""
    response = client.get('/')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    products = data['products']
    
    # Find the heavy product
    heavy_product = next((p for p in products if p['id'] == 3), None)
    assert heavy_product is not None
    
    assert heavy_product['name'] == "Heavy Product"
    assert heavy_product['description'] == "Heavy product for shipping tests"
    assert heavy_product['price'] == 50.0  # $50.00
    assert heavy_product['weight'] == 3000
    assert heavy_product['image'] == "heavy.jpg"
    assert heavy_product['in_stock'] == True
