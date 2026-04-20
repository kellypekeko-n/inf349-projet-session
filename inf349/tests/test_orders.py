import json


# ── Helpers ────────────────────────────────────────────────────────────────────

def _post_order(client, product_id=1, quantity=2):
    resp = client.post(
        "/order",
        json={"product": {"id": product_id, "quantity": quantity}},
        content_type="application/json",
    )
    return resp


def _get_order(client, resp_302):
    oid = resp_302.headers["Location"].split("/")[-1]
    return client.get(f"/order/{oid}")


# ── POST /order ────────────────────────────────────────────────────────────────

def test_create_order_success(client):
    resp = _post_order(client, product_id=1, quantity=2)
    assert resp.status_code == 302
    assert "Location" in resp.headers

    order = _get_order(client, resp).get_json()["order"]
    # id=1 prix=2810 cts, qty=2 → total=5620, poids=800g → shipping=1000
    assert order["products"][0]["id"] == 1
    assert order["products"][0]["quantity"] == 2
    assert order["total_price"] == 5620
    assert order["shipping_price"] == 1000
    assert order["paid"] is False
    assert order["email"] is None
    assert order["credit_card"] == {}
    assert order["transaction"] == {}


def test_create_order_missing_product(client):
    resp = client.post("/order", json={}, content_type="application/json")
    assert resp.status_code == 422
    data = resp.get_json()
    assert data["errors"]["product"]["code"] == "missing-fields"


def test_create_order_missing_fields(client):
    resp = client.post("/order", json={"product": {"id": 1}}, content_type="application/json")
    assert resp.status_code == 422
    assert resp.get_json()["errors"]["product"]["code"] == "missing-fields"


def test_create_order_invalid_quantity(client):
    resp = client.post(
        "/order", json={"product": {"id": 1, "quantity": 0}}, content_type="application/json"
    )
    assert resp.status_code == 422
    assert resp.get_json()["errors"]["product"]["code"] == "missing-fields"


def test_create_order_out_of_inventory(client):
    # id=4 est hors stock
    resp = client.post(
        "/order", json={"product": {"id": 4, "quantity": 1}}, content_type="application/json"
    )
    assert resp.status_code == 422
    assert resp.get_json()["errors"]["product"]["code"] == "out-of-inventory"


def test_create_order_nonexistent_product(client):
    resp = client.post(
        "/order", json={"product": {"id": 999, "quantity": 1}}, content_type="application/json"
    )
    assert resp.status_code == 422
    assert resp.get_json()["errors"]["product"]["code"] == "missing-fields"


# ── GET /order/<id> ────────────────────────────────────────────────────────────

def test_get_order_not_found(client):
    assert client.get("/order/99999").status_code == 404


def test_get_order_success(client, sample_order):
    # sample_order : 2 × id=1 → total=5620, shipping=1000
    resp = client.get(f"/order/{sample_order.id}")
    assert resp.status_code == 200
    order = resp.get_json()["order"]
    assert order["id"] == sample_order.id
    assert order["products"][0]["id"] == 1
    assert order["products"][0]["quantity"] == 2
    assert order["total_price"] == 5620
    assert order["shipping_price"] == 1000
    assert order["paid"] is False


# ── PUT /order/<id> ────────────────────────────────────────────────────────────

SHIPPING = {
    "country": "Canada",
    "address": "123 Test St",
    "postal_code": "G7X 3Y7",
    "city": "Chicoutimi",
    "province": "QC",
}


def test_update_order_customer_info_success(client, sample_order):
    resp = client.put(
        f"/order/{sample_order.id}",
        json={"order": {"email": "test@example.com", "shipping_information": SHIPPING}},
        content_type="application/json",
    )
    assert resp.status_code == 200
    order = resp.get_json()["order"]
    assert order["email"] == "test@example.com"
    assert order["shipping_information"]["province"] == "QC"
    # Taxe QC 15% sur total_price uniquement (pas le shipping)
    # total_price=5620, tax=5620*0.15=843 → total_price_tax=6463
    assert abs(order["total_price_tax"] - 6463.0) < 0.5


def test_update_order_missing_fields(client, sample_order):
    resp = client.put(
        f"/order/{sample_order.id}",
        json={"order": {"email": "t@t.com", "shipping_information": {"country": "Canada"}}},
        content_type="application/json",
    )
    assert resp.status_code == 422
    assert resp.get_json()["errors"]["order"]["code"] == "missing-fields"


def test_update_order_not_found(client):
    resp = client.put(
        "/order/99999",
        json={"order": {"email": "t@t.com", "shipping_information": SHIPPING}},
        content_type="application/json",
    )
    assert resp.status_code == 404


# ── Calcul frais d'expédition ──────────────────────────────────────────────────

def test_shipping_price_light(client):
    # 1 × id=1 (400g ≤ 500g) → shipping = 500
    resp = _post_order(client, product_id=1, quantity=1)
    assert resp.status_code == 302
    order = _get_order(client, resp).get_json()["order"]
    assert order["shipping_price"] == 500


def test_shipping_price_medium(client):
    # 2 × id=1 (800g, 500 < 800 < 2000) → shipping = 1000
    resp = _post_order(client, product_id=1, quantity=2)
    assert resp.status_code == 302
    order = _get_order(client, resp).get_json()["order"]
    assert order["shipping_price"] == 1000


def test_shipping_price_heavy(client):
    # 1 × id=3 (3000g ≥ 2000g) → shipping = 2500
    resp = _post_order(client, product_id=3, quantity=1)
    assert resp.status_code == 302
    order = _get_order(client, resp).get_json()["order"]
    assert order["shipping_price"] == 2500
