import os

import requests
from rq import Queue
from redis import Redis

from .models import Product, Order, OrderItem, ShippingInformation
from .utils import calculate_shipping_price, calculate_total_with_tax
from .errors import BusinessError


def get_redis_client():
    redis_url = os.environ.get("REDIS_URL", "redis://localhost")
    return Redis.from_url(redis_url)


def _clean_string(value):
    """Supprime les caractères NUL (0x00) incompatibles avec PostgreSQL."""
    if isinstance(value, str):
        return value.replace("\x00", "")
    return value


class ProductService:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/") + "/"

    def fetch_products(self):
        url = f"{self.base_url}products.json"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise BusinessError(
                message=f"Impossible de récupérer les produits distants: {exc}",
                code="product-service-unavailable",
                status_code=500,
                field="product",
            )

        products = []
        for product_data in payload.get("products", []):
            product, _ = Product.get_or_create(
                id=product_data["id"],
                defaults={
                    "name": _clean_string(product_data["name"]),
                    "description": _clean_string(product_data["description"]),
                    "price": int(round(float(product_data["price"]) * 100)),
                    "in_stock": product_data["in_stock"],
                    "weight": product_data["weight"],
                    "image": _clean_string(product_data["image"]),
                },
            )

            product.name = _clean_string(product_data["name"])
            product.description = _clean_string(product_data["description"])
            product.price = int(round(float(product_data["price"]) * 100))
            product.in_stock = product_data["in_stock"]
            product.weight = product_data["weight"]
            product.image = _clean_string(product_data["image"])
            product.save()

            products.append(product)

        return products


class PaymentService:
    def __init__(self, base_url):
        self.base_url = base_url

    def process_payment(self, credit_card_info, amount):
        payload = {
            "credit_card": credit_card_info,
            "amount_charged": int(amount),
        }

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=30,
                headers={"Accept": "application/json"},
            )
            print("PAYMENT STATUS:", response.status_code)
            print("PAYMENT BODY:", response.text)

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "credit_card": data["credit_card"],
                    "transaction": data["transaction"],
                }

            # Erreur retournée par le service distant (422, etc.)
            try:
                data = response.json()
            except Exception:
                data = {
                    "errors": {
                        "credit_card": {
                            "code": "payment-error",
                            "name": response.text or f"Erreur HTTP {response.status_code}",
                        }
                    }
                }

            return {
                "success": False,
                "error": data,
                "status_code": response.status_code,
            }

        except Exception as exc:
            print("PAYMENT GENERAL ERROR:", repr(exc))
            return {
                "success": False,
                "error": {
                    "errors": {
                        "credit_card": {
                            "code": "payment-service-unavailable",
                            "name": str(exc),
                        }
                    }
                },
                "status_code": 500,
            }


class OrderService:

    @staticmethod
    def create_order(products_list):
        items = []
        for entry in products_list:
            try:
                product = Product.get_by_id(entry["id"])
            except Product.DoesNotExist:
                raise BusinessError(
                    message="La création d'une commande nécessite un produit",
                    code="missing-fields",
                    status_code=422,
                    field="product",
                )

            if not product.in_stock:
                raise BusinessError(
                    message="Le produit demandé n'est pas en inventaire",
                    code="out-of-inventory",
                    status_code=422,
                    field="product",
                )

            items.append((product, entry["quantity"]))

        total_price = sum(p.price * q for p, q in items)
        total_weight = sum(p.weight * q for p, q in items)
        shipping_price = calculate_shipping_price(total_weight)
        total_price_tax = calculate_total_with_tax(total_price, shipping_price, province=None)

        order = Order.create(
            total_price=total_price,
            shipping_price=shipping_price,
            total_price_tax=total_price_tax,
            paid=False,
            payment_status="pending",
        )

        for product, quantity in items:
            OrderItem.create(order=order, product=product, quantity=quantity)

        return order

    @staticmethod
    def get_order(order_id):
        try:
            return Order.select().where(Order.id == order_id).get()
        except Order.DoesNotExist:
            return None

    @staticmethod
    def update_order_info(order_id, email, shipping_info):
        order = OrderService.get_order(order_id)
        if not order:
            return None

        if order.paid:
            raise BusinessError(
                message="La commande a déjà été payée.",
                code="already-paid",
                status_code=422,
                field="order",
            )

        if order.payment_status == "processing":
            raise BusinessError(
                message="La commande est en cours de paiement.",
                code="payment-in-progress",
                status_code=409,
                field="order",
            )

        if order.shipping_information:
            shipping = order.shipping_information
            shipping.country = shipping_info["country"]
            shipping.address = shipping_info["address"]
            shipping.postal_code = shipping_info["postal_code"]
            shipping.city = shipping_info["city"]
            shipping.province = shipping_info["province"]
            shipping.save()
        else:
            shipping = ShippingInformation.create(
                country=shipping_info["country"],
                address=shipping_info["address"],
                postal_code=shipping_info["postal_code"],
                city=shipping_info["city"],
                province=shipping_info["province"],
            )

        order.email = email
        order.shipping_information = shipping
        order.total_price_tax = calculate_total_with_tax(
            order.total_price,
            order.shipping_price,
            shipping.province,
        )
        order.save()

        return order

    @staticmethod
    def enqueue_payment(order_id, credit_card_info, payment_service_url):
        order = OrderService.get_order(order_id)
        if not order:
            return None

        if order.paid:
            raise BusinessError(
                message="La commande a déjà été payée.",
                code="already-paid",
                status_code=422,
                field="order",
            )

        if order.payment_status == "processing":
            raise BusinessError(
                message="La commande est en cours de paiement.",
                code="payment-in-progress",
                status_code=409,
                field="order",
            )

        if not order.email or not order.shipping_information:
            raise BusinessError(
                message="Les informations du client sont nécessaire avant d'appliquer une carte de crédit",
                code="missing-fields",
                status_code=422,
                field="order",
            )

        order.payment_status = "processing"
        order.save()

        # Invalider le cache Redis pour que GET renvoie 202 pendant le traitement
        try:
            get_redis_client().delete(f"order:{order_id}")
        except Exception:
            pass

        from .tasks import process_payment
        q = Queue(connection=get_redis_client())
        q.enqueue(process_payment, order_id, credit_card_info, payment_service_url)

        return order