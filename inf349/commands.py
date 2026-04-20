import os

import click
import redis
from flask import current_app
from flask.cli import with_appcontext
from rq import Queue
from rq.worker import SimpleWorker
from rq.timeouts import BaseDeathPenalty

from werkzeug.security import generate_password_hash
from .models import db, Product, Order, OrderItem, ShippingInformation, CreditCard, Transaction, User
from .services import ProductService


class WindowsDeathPenalty(BaseDeathPenalty):
    """Remplace SIGALRM (Unix uniquement) par un no-op pour Windows."""
    def setup_death_penalty(self):
        pass

    def cancel_death_penalty(self):
        pass


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize the database tables and fetch products from remote service."""
    if db.is_closed():
        db.connect()

    db.drop_tables(
        [OrderItem, Order, Product, ShippingInformation, CreditCard, Transaction],
        safe=True,
    )
    db.create_tables(
        [Product, ShippingInformation, CreditCard, Transaction, Order, OrderItem, User],
        safe=True,
    )

    # Créer les comptes par défaut s'ils n'existent pas
    default_users = [
        {"username": "kelly", "password": "1234",    "is_admin": False},
        {"username": "admin", "password": "admin123", "is_admin": True},
    ]
    for u in default_users:
        User.get_or_create(
            username=u["username"],
            defaults={
                "password_hash": generate_password_hash(u["password"]),
                "is_admin": u["is_admin"],
            },
        )
    click.echo("Default users created (kelly, admin).")

    product_service = ProductService(current_app.config["PRODUCT_SERVICE_URL"])

    try:
        products = product_service.fetch_products()
        click.echo(f"Successfully initialized database with {len(products)} products.")
        click.echo("Database initialized successfully.")
    except Exception as e:
        click.echo(f"Error fetching products: {e}")
        raise
    finally:
        if not db.is_closed():
            db.close()


@click.command("worker")
@with_appcontext
def worker_command():
    """Lance le worker RQ pour traiter les tâches de paiement en arrière-plan."""
    redis_url = os.environ.get("REDIS_URL", "redis://localhost")
    conn = redis.from_url(redis_url)

    click.echo(f"Starting RQ worker on {redis_url}...")

    q = Queue(connection=conn)
    worker = SimpleWorker([q], connection=conn)
    worker.death_penalty_class = WindowsDeathPenalty
    worker.work()