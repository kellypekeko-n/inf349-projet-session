import json
import os

from flask import Blueprint, request, jsonify, url_for, current_app, redirect, session
from redis import Redis
from werkzeug.security import generate_password_hash, check_password_hash

from .models import Product, User, db, Transaction
from .services import OrderService, ProductService
from .utils import (
    validate_order_creation,
    validate_order_update,
    validate_payment_data,
    format_order_response,
    normalize_products_payload,
    shipping_price_cents,
    TAX_RATES,
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
    if not current_app.testing:
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

        if current_app.testing:
            # En mode test : paiement synchrone (pas de worker RQ)
            if order.paid:
                raise BusinessError(
                    message="La commande a déjà été payée.",
                    code="already-paid",
                    status_code=422,
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
            from .tasks import process_payment
            try:
                process_payment(order_id, data["credit_card"], current_app.config["PAYMENT_SERVICE_URL"])
            except Exception:
                pass
            # process_payment ferme la DB — la rouvrir
            if db.is_closed():
                db.connect()
            refreshed = OrderService.get_order(order_id)
            if refreshed.paid:
                return jsonify(format_order_response(refreshed)), 200
            # Paiement échoué — retourner l'erreur de la transaction
            error_code, error_name = "payment-error", "Paiement échoué"
            if refreshed.transaction_id:
                tx = Transaction.get_by_id(refreshed.transaction_id)
                if tx.error_code:
                    error_code = tx.error_code
                    error_name = tx.error_name or error_name
            raise ValidationError([{"field": "credit_card", "code": error_code, "name": error_name}])

        OrderService.enqueue_payment(
            order_id=order_id,
            credit_card_info=data["credit_card"],
            payment_service_url=current_app.config["PAYMENT_SERVICE_URL"],
        )
        return "", 202


# ── AUTH ──────────────────────────────────────────────────────────────────────

def is_admin():
    return session.get("is_admin", False)


@bp.route("/login", methods=["POST"])
def login_route():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").lower().strip()
    password = data.get("password", "")
    try:
        user = User.get(User.username == username)
        if check_password_hash(user.password_hash, password):
            session["user"] = username
            session["is_admin"] = user.is_admin
            return jsonify({"user": username, "is_admin": user.is_admin})
    except User.DoesNotExist:
        pass
    return jsonify({"error": "Identifiants invalides"}), 401


@bp.route("/register", methods=["POST"])
def register_route():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").lower().strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Nom d'utilisateur et mot de passe requis"}), 422
    if len(username) < 3:
        return jsonify({"error": "Le nom d'utilisateur doit contenir au moins 3 caractères"}), 422
    if len(password) < 4:
        return jsonify({"error": "Le mot de passe doit contenir au moins 4 caractères"}), 422

    try:
        User.get(User.username == username)
        return jsonify({"error": "Ce nom d'utilisateur est déjà pris"}), 409
    except User.DoesNotExist:
        pass

    User.create(
        username=username,
        password_hash=generate_password_hash(password),
        is_admin=False,
    )
    session["user"] = username
    session["is_admin"] = False
    return jsonify({"user": username, "is_admin": False}), 201


@bp.route("/logout", methods=["POST"])
def logout_route():
    session.clear()
    return jsonify({"message": "ok"})


@bp.route("/me", methods=["GET"])
def me():
    user = session.get("user")
    return jsonify({"user": user, "is_admin": session.get("is_admin", False) if user else False})


# ── ADMIN ─────────────────────────────────────────────────────────────────────

@bp.route("/admin/orders", methods=["GET"])
def admin_orders_api():
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
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
    if not is_admin():
        return jsonify({"error": "Accès refusé"}), 403
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
