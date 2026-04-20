import json


def test_get_products(client):
    response = client.get("/")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert "products" in data
    assert len(data["products"]) == 4  # id=1,2,3,4

    product = data["products"][0]
    for key in ("id", "name", "description", "price", "in_stock", "weight", "image"):
        assert key in product

    # Le prix est en dollars (pas en cents)
    assert isinstance(product["price"], (int, float))
    assert product["price"] > 0


def test_get_products_includes_out_of_stock(client):
    response = client.get("/")
    data = json.loads(response.data)
    products = data["products"]

    in_stock = [p for p in products if p["in_stock"]]
    out_of_stock = [p for p in products if not p["in_stock"]]

    assert len(in_stock) == 3
    assert len(out_of_stock) == 1
    assert out_of_stock[0]["id"] == 4
    assert out_of_stock[0]["in_stock"] is False


def test_product_data_integrity(client):
    response = client.get("/")
    data = json.loads(response.data)
    products = data["products"]

    heavy = next((p for p in products if p["id"] == 3), None)
    assert heavy is not None
    assert heavy["name"] == "Produit Lourd"
    assert heavy["price"] == 50.0   # 5000 cents → $50.00
    assert heavy["weight"] == 3000
    assert heavy["in_stock"] is True
