from flask import Blueprint, render_template

ui_bp = Blueprint("ui", __name__)


@ui_bp.route("/ui", methods=["GET"])
def ui_index():
    return render_template("index.html")


@ui_bp.route("/ui/order/<int:order_id>", methods=["GET"])
def ui_order(order_id):
    return render_template("order.html", order_id=order_id)


@ui_bp.route("/ui/orders", methods=["GET"])
def ui_orders():
    return render_template("orders.html")
