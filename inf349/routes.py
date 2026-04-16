import json
import os

from flask import Blueprint, request, jsonify, url_for, current_app, redirect, session
from redis import Redis

from .models import Product
from .services import OrderService, ProductService
from .utils import (
    validate_order_creation,
    validate_order_update,
    validate_payment_data,
    format_order_response,
    normalize_products_payload,
)
from .errors import (
    ValidationError,
    NotFoundError,
    BusinessError,
    handle_validation_error,
    handle_not_found_error,
    handle_business_error,
)

bp = Blueprint("api", __name__)


def get_redis_client():
    redis_url = os.environ.get("REDIS_URL", "redis://localhost")
    return Redis.from_url(redis_url)


@bp.route("/", methods=["GET"])
def get_products():
    # Redirect browsers to the HTML interface
    if request.accept_mimetypes.best_match(["application/json", "text/html"]) == "text/html":
        return redirect("/ui")

    if Product.select().count() == 0:
        ProductService(current_app.config["PRODUCT_SERVICE_URL"]).fetch_products()

    products_list = []
    for product in Product.select():
        products_list.append({
            "name": product.name,
            "id": product.id,
            "in_stock": product.in_stock,
            "description": product.description,
            "price": round(product.price / 100, 2),
            "weight": product.weight,
            "image": product.image,
        })

    return jsonify({"products": products_list}), 200


@bp.route("/order", methods=["POST"])
def create_order():
    data = request.get_json(silent=True)

    if not data:
        raise ValidationError([{
            "field": "product",
            "code": "missing-fields",
            "name": "La création d'une commande nécessite un produit",
        }])

    errors = validate_order_creation(data)
    if errors:
        raise ValidationError(errors)

    products_list = normalize_products_payload(data)
    order = OrderService.create_order(products_list)

    response = jsonify({})
    response.status_code = 302
    response.headers["Location"] = url_for("api.get_order", order_id=order.id)
    return response


@bp.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id):
    try:
        r = get_redis_client()
        cached = r.get(f"order:{order_id}")
        if cached:
            return jsonify(json.loads(cached)), 200
    except Exception:
        pass

    order = OrderService.get_order(order_id)
    if not order:
        raise NotFoundError(field="order", message="La commande demandée est introuvable.")

    if order.payment_status == "processing":
        return "", 202

    return jsonify(format_order_response(order)), 200


@bp.route("/order/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    data = request.get_json(silent=True)

    if not data:
        raise ValidationError([{
            "field": "order",
            "code": "missing-fields",
            "name": "Il manque un ou plusieurs champs qui sont obligatoires",
        }])

    order = OrderService.get_order(order_id)
    if not order:
        raise NotFoundError(field="order", message="La commande demandée est introuvable.")

    has_order = "order" in data
    has_credit_card = "credit_card" in data

    if has_order and has_credit_card:
        raise ValidationError([{
            "field": "order",
            "code": "missing-fields",
            "name": "Les informations de client et de paiement doivent être envoyées séparément",
        }])

    if not has_order and not has_credit_card:
        raise ValidationError([{
            "field": "order",
            "code": "missing-fields",
            "name": "Il manque un ou plusieurs champs qui sont obligatoires",
        }])

    if has_order:
        if order.payment_status == "processing":
            return "", 409

        errors = validate_order_update(data)
        if errors:
            raise ValidationError(errors)

        order_data = data["order"]
        updated_order = OrderService.update_order_info(
            order_id=order_id,
            email=order_data["email"],
            shipping_info=order_data["shipping_information"],
        )
        return jsonify(format_order_response(updated_order)), 200

    if has_credit_card:
        if order.payment_status == "processing":
            return "", 409

        errors = validate_payment_data(data)
        if errors:
            raise ValidationError(errors)

        OrderService.enqueue_payment(
            order_id=order_id,
            credit_card_info=data["credit_card"],
            payment_service_url=current_app.config["PAYMENT_SERVICE_URL"],
        )
        return "", 202


# ── AUTH ──────────────────────────────────────────────────────────────────────

USERS = {
    "kelly": "1234",
    "admin": "admin123",
}


@bp.route("/login", methods=["POST"])
def login_route():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").lower().strip()
    password = data.get("password", "")
    if USERS.get(username) == password:
        session["user"] = username
        return jsonify({"user": username})
    return jsonify({"error": "Identifiants invalides"}), 401


@bp.route("/logout", methods=["POST"])
def logout_route():
    session.clear()
    return jsonify({"message": "ok"})


@bp.route("/me", methods=["GET"])
def me():
    return jsonify({"user": session.get("user")})


# ── ADMIN ─────────────────────────────────────────────────────────────────────

@bp.route("/admin/orders", methods=["GET"])
def admin_orders_api():
    from .models import Order
    orders = []
    for o in Order.select().order_by(Order.id.desc()).limit(100):
        orders.append({
            "id": o.id,
            "paid": o.paid,
            "payment_status": o.payment_status,
            "total_price": o.total_price,
            "shipping_price": o.shipping_price,
            "email": o.email,
        })
    return jsonify({"orders": orders})


@bp.route("/admin/stats", methods=["GET"])
def admin_stats_api():
    from .models import Order
    total = Order.select().count()
    paid_list = list(Order.select().where(Order.paid == True))
    paid_count = len(paid_list)
    revenue = sum(o.total_price + o.shipping_price for o in paid_list)
    processing = Order.select().where(Order.payment_status == "processing").count()
    pending = Order.select().where(Order.payment_status == "pending").count()
    return jsonify({
        "total_orders": total,
        "paid_orders": paid_count,
        "pending_orders": pending,
        "processing_orders": processing,
        "revenue_cents": revenue,
    })


# ── ERROR HANDLERS ────────────────────────────────────────────────────────────

@bp.errorhandler(ValidationError)
def handle_validation_exception(error):
    return handle_validation_error(error)


@bp.errorhandler(NotFoundError)
def handle_not_found_exception(error):
    return handle_not_found_error(error)


@bp.errorhandler(BusinessError)
def handle_business_exception(error):
    return handle_business_error(error)
