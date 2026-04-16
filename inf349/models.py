import os
from datetime import datetime
from peewee import (
    Model,
    IntegerField,
    CharField,
    TextField,
    BooleanField,
    ForeignKeyField,
    DecimalField,
    DateTimeField,
)
from playhouse.postgres_ext import PostgresqlExtDatabase

db = PostgresqlExtDatabase(
    os.environ.get("DB_NAME"),
    host=os.environ.get("DB_HOST"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    port=int(os.environ.get("DB_PORT", 5432)),
)


class BaseModel(Model):
    class Meta:
        database = db


class Product(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    description = TextField()
    price = IntegerField()  # en cents
    in_stock = BooleanField(default=True)
    weight = IntegerField()  # en grammes
    image = CharField()

    class Meta:
        table_name = "products"


class ShippingInformation(BaseModel):
    country = CharField()
    address = CharField()
    postal_code = CharField()
    city = CharField()
    province = CharField()

    class Meta:
        table_name = "shipping_information"


class CreditCard(BaseModel):
    name = CharField()
    first_digits = CharField()
    last_digits = CharField()
    expiration_year = IntegerField()
    expiration_month = IntegerField()

    class Meta:
        table_name = "credit_cards"


class Transaction(BaseModel):
    id = CharField(primary_key=True)
    success = BooleanField()
    amount_charged = IntegerField()
    error_code = CharField(null=True)
    error_name = CharField(null=True)

    class Meta:
        table_name = "transactions"


class Order(BaseModel):
    total_price = IntegerField()  # prix des produits * quantités
    shipping_price = IntegerField()  # en cents
    total_price_tax = DecimalField(max_digits=12, decimal_places=2, default=0)
    email = CharField(null=True)
    shipping_information = ForeignKeyField(
        ShippingInformation, null=True, backref="orders"
    )
    credit_card = ForeignKeyField(CreditCard, null=True, backref="orders")
    transaction = ForeignKeyField(Transaction, null=True, backref="orders")
    paid = BooleanField(default=False)
    payment_status = CharField(default="pending")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "orders"


class OrderItem(BaseModel):
    order = ForeignKeyField(Order, backref="items", on_delete="CASCADE")
    product = ForeignKeyField(Product, backref="order_items")
    quantity = IntegerField()

    class Meta:
        table_name = "order_items"


def initialize_db(database):
    if database.is_closed():
        database.connect()

    database.create_tables(
        [Product, ShippingInformation, CreditCard, Transaction, Order, OrderItem],
        safe=True,
    )
