from decimal import Decimal, ROUND_HALF_UP

TAX_RATES = {
    "QC": 0.15,
    "ON": 0.13,
    "AB": 0.05,
    "BC": 0.12,
    "NS": 0.14,
}


def shipping_price_cents(total_weight_grams):
    if total_weight_grams <= 500:
        return 500
    if total_weight_grams < 2000:
        return 1000
    return 2500


# backward-compatible alias
calculate_shipping_price = shipping_price_cents


def calculate_tax(amount_cents, province):
    rate_float = TAX_RATES.get(province)
    if rate_float is None:
        return Decimal("0.00")

    rate = Decimal(str(rate_float))
    tax = Decimal(amount_cents) * rate
    return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_total_with_tax(total_price_cents, _shipping_price_cents, province=None):
    # total_price_tax = total_price * (1 + tax_rate)
    # Shipping is NOT included in the taxable base (see spec example: 9148 * 1.15 = 10520.20)
    product_total = Decimal(total_price_cents)

    if not province:
        return product_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    tax = calculate_tax(product_total, province)
    return (product_total + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def normalize_products_payload(data):
    if "products" in data and isinstance(data["products"], list):
        return data["products"]
    if "product" in data and isinstance(data["product"], dict):
        return [data["product"]]
    return None


def validate_order_creation(data):
    products = normalize_products_payload(data)

    if products is None or len(products) == 0:
        return [{
            "field": "product",
            "code": "missing-fields",
            "name": "La création d'une commande nécessite un produit",
        }]

    for item in products:
        if not isinstance(item, dict) or "id" not in item or "quantity" not in item:
            return [{
                "field": "product",
                "code": "missing-fields",
                "name": "La création d'une commande nécessite un produit",
            }]
        quantity = item.get("quantity")
        if not isinstance(quantity, int) or quantity < 1:
            return [{
                "field": "product",
                "code": "missing-fields",
                "name": "La création d'une commande nécessite un produit",
            }]

    return []


def validate_order_update(data):
    errors = []

    order_data = data.get("order")
    if not order_data or not isinstance(order_data, dict):
        return [{
            "field": "order",
            "code": "missing-fields",
            "name": "Il manque un ou plusieurs champs qui sont obligatoires",
        }]

    forbidden_fields = {
        "total_price",
        "total_price_tax",
        "transaction",
        "paid",
        "product",
        "products",
        "shipping_price",
        "id",
        "credit_card",
    }

    if any(field in order_data for field in forbidden_fields):
        return [{
            "field": "order",
            "code": "missing-fields",
            "name": "Il manque un ou plusieurs champs qui sont obligatoires",
        }]

    if not order_data.get("email"):
        errors.append({
            "field": "order",
            "code": "missing-fields",
            "name": "Il manque un ou plusieurs champs qui sont obligatoires",
        })

    shipping_info = order_data.get("shipping_information")
    if not shipping_info or not isinstance(shipping_info, dict):
        errors.append({
            "field": "order",
            "code": "missing-fields",
            "name": "Il manque un ou plusieurs champs qui sont obligatoires",
        })
        return errors

    required_shipping_fields = ["country", "address", "postal_code", "city", "province"]
    for field in required_shipping_fields:
        if not shipping_info.get(field):
            errors.append({
                "field": "order",
                "code": "missing-fields",
                "name": "Il manque un ou plusieurs champs qui sont obligatoires",
            })
            break

    return errors


def validate_payment_data(data):
    credit_card = data.get("credit_card")
    if not credit_card or not isinstance(credit_card, dict):
        return [{
            "field": "credit_card",
            "code": "missing-fields",
            "name": "Les informations de carte de crédit sont requises",
        }]

    required_fields = ["name", "number", "expiration_year", "expiration_month", "cvv"]
    for field in required_fields:
        if field not in credit_card or credit_card.get(field) in (None, ""):
            return [{
                "field": "credit_card",
                "code": "missing-fields",
                "name": "Les informations de carte de crédit sont requises",
            }]

    return []


def format_order_response(order):
    products = [
        {"id": item.product_id, "quantity": item.quantity}
        for item in order.items
    ]

    response = {
        "order": {
            "id": order.id,
            "total_price": order.total_price,
            "total_price_tax": round(float(order.total_price_tax), 2) if order.total_price_tax is not None else 0,
            "email": order.email,
            "credit_card": {},
            "shipping_information": {},
            "paid": order.paid,
            "transaction": {},
            "products": products,
            "shipping_price": order.shipping_price,
        }
    }

    if order.shipping_information:
        response["order"]["shipping_information"] = {
            "country": order.shipping_information.country,
            "address": order.shipping_information.address,
            "postal_code": order.shipping_information.postal_code,
            "city": order.shipping_information.city,
            "province": order.shipping_information.province,
        }

    if order.credit_card:
        response["order"]["credit_card"] = {
            "name": order.credit_card.name,
            "first_digits": order.credit_card.first_digits,
            "last_digits": order.credit_card.last_digits,
            "expiration_year": order.credit_card.expiration_year,
            "expiration_month": order.credit_card.expiration_month,
        }

    if order.transaction:
        error = {}
        if order.transaction.error_code:
            error = {
                "code": order.transaction.error_code,
                "name": order.transaction.error_name,
            }
        response["order"]["transaction"] = {
            "id": order.transaction.id,
            "success": order.transaction.success,
            "error": error,
            "amount_charged": order.transaction.amount_charged,
        }

    return response