import os
from flask import Flask
from .models import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        REDIS_URL=os.environ.get("REDIS_URL", "redis://localhost"),
        PRODUCT_SERVICE_URL="https://dimensweb.uqac.ca/~jgnault/shops/products/",
        PAYMENT_SERVICE_URL="https://dimensweb.uqac.ca/~jgnault/shops/pay/",
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    @app.before_request
    def _connect_db():
        if db.is_closed():
            db.connect()

    @app.teardown_request
    def _close_db(exception):
        if not db.is_closed():
            db.close()

    from . import commands
    app.cli.add_command(commands.init_db_command)
    app.cli.add_command(commands.worker_command)

    from . import routes
    app.register_blueprint(routes.bp)

    from . import ui
    app.register_blueprint(ui.ui_bp)

    return app