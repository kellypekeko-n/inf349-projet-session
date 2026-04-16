import json
import os

from redis import Redis

from .models import db, Order, CreditCard, Transaction
from .services import PaymentService
from .utils import format_order_response


def _cache_order_in_redis(order):
    redis_url = os.environ.get("REDIS_URL", "redis://localhost")
    r = Redis.from_url(redis_url)
    payload = format_order_response(order)
    r.set(f"order:{order.id}", json.dumps(payload))


def process_payment(order_id, credit_card_info, payment_service_url):
    if db.is_closed():
        db.connect()

    order = None
    try:
        order = Order.select().where(Order.id == order_id).get()

        amount_to_charge = int(round(float(order.total_price_tax)))

        payment_service = PaymentService(payment_service_url)
        result = payment_service.process_payment(credit_card_info, amount_to_charge)

        if result["success"]:
            credit_card = CreditCard.create(
                name=result["credit_card"]["name"],
                first_digits=result["credit_card"]["first_digits"],
                last_digits=result["credit_card"]["last_digits"],
                expiration_year=result["credit_card"]["expiration_year"],
                expiration_month=result["credit_card"]["expiration_month"],
            )
            transaction = Transaction.create(
                id=result["transaction"]["id"],
                success=True,
                amount_charged=result["transaction"]["amount_charged"],
            )
            order.credit_card = credit_card
            order.transaction = transaction
            order.paid = True
            order.payment_status = "paid"
            order.save()
            # Mettre en cache uniquement les commandes payées (spec remise 2)
            _cache_order_in_redis(order)
        else:
            cc_error = result["error"].get("errors", {}).get("credit_card", {})
            transaction = Transaction.create(
                id=f"failed-{order_id}",
                success=False,
                amount_charged=amount_to_charge,
                error_code=cc_error.get("code"),
                error_name=cc_error.get("name"),
            )
            order.transaction = transaction
            order.payment_status = "failed"
            order.save()

    except Exception:
        if order is not None:
            order.payment_status = "failed"
            order.save()
        raise

    finally:
        if not db.is_closed():
            db.close()
