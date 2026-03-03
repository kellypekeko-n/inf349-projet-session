import os
from flask import Flask
from peewee import SqliteDatabase

db = SqliteDatabase(None)  # Deferred initialization

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'database.db'),
        PRODUCT_SERVICE_URL="http://dimensweb.uqac.ca/~jgnault/shops/products/",
        PAYMENT_SERVICE_URL="http://dimensweb.uqac.ca/~jgnault/shops/pay/"
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init(app.config['DATABASE'])

    from . import models
    models.initialize_db(db)

    from . import commands
    app.cli.add_command(commands.init_db_command)

    from . import routes
    app.register_blueprint(routes.bp)

    return app
