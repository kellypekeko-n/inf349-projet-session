import json
from datetime import datetime
from peewee import *
from . import db

class Product(Model):
    id = IntegerField(primary_key=True)
    name = CharField()
    description = TextField()
    price = IntegerField()  # Price in cents
    in_stock = BooleanField(default=True)
    weight = IntegerField()  # Weight in grams
    image = CharField()

    class Meta:
        database = db
        table_name = 'products'

class ShippingInformation(Model):
    country = CharField()
    address = CharField()
    postal_code = CharField()
    city = CharField()
    province = CharField()

    class Meta:
        database = db
        table_name = 'shipping_information'

class CreditCard(Model):
    name = CharField()
    first_digits = CharField()
    last_digits = CharField()
    expiration_year = IntegerField()
    expiration_month = IntegerField()

    class Meta:
        database = db
        table_name = 'credit_cards'

class Transaction(Model):
    id = CharField(primary_key=True)
    success = BooleanField()
    amount_charged = IntegerField()

    class Meta:
        database = db
        table_name = 'transactions'

class Order(Model):
    product = ForeignKeyField(Product, backref='orders')
    quantity = IntegerField()
    total_price = IntegerField()  # Price in cents (product price * quantity)
    shipping_price = IntegerField()  # Shipping price in cents
    total_price_tax = DecimalField(decimal_places=2, max_digits=10)  # Price with tax
    email = CharField(null=True)
    shipping_information = ForeignKeyField(ShippingInformation, null=True, backref='orders')
    credit_card = ForeignKeyField(CreditCard, null=True, backref='orders')
    transaction = ForeignKeyField(Transaction, null=True, backref='orders')
    paid = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        table_name = 'orders'

def initialize_db(database):
    database.connect()
    database.create_tables([Product, ShippingInformation, CreditCard, Transaction, Order], safe=True)
    database.close()
