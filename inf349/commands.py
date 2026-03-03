import click
from flask import current_app
from . import db
from .models import Product, Order, ShippingInformation, CreditCard, Transaction
from .services import ProductService

@click.command('init-db')
def init_db_command():
    """Initialize the database with products from remote service"""
    db.drop_tables([Product, Order, ShippingInformation, CreditCard, Transaction])
    db.create_tables([Product, Order, ShippingInformation, CreditCard, Transaction])
    
    # Fetch products from remote service
    product_service = ProductService(current_app.config['PRODUCT_SERVICE_URL'])
    try:
        products = product_service.fetch_products()
        click.echo(f'Successfully initialized database with {len(products)} products.')
    except Exception as e:
        click.echo(f'Error fetching products: {e}')
        db.rollback()
        raise e
    
    db.close()
    click.echo('Database initialized successfully.')

@click.command('fetch-products')
def fetch_products_command():
    """Fetch products from remote service (useful for testing)"""
    product_service = ProductService(current_app.config['PRODUCT_SERVICE_URL'])
    try:
        products = product_service.fetch_products()
        click.echo(f'Successfully fetched {len(products)} products.')
    except Exception as e:
        click.echo(f'Error fetching products: {e}')
        raise e
