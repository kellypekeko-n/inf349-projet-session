from flask import Blueprint, request, jsonify, url_for
from .models import Product, Order
from .services import OrderService
from .utils import validate_order_creation, validate_order_update, validate_payment_data, format_order_response
from .errors import ValidationError, NotFoundError, BusinessError, handle_validation_error, handle_api_error, handle_not_found_error
from . import db

bp = Blueprint('api', __name__)

@bp.route('/', methods=['GET'])
def get_products():
    """Get all products"""
    if not db.is_connection_usable():
        db.connect()
    
    try:
        products = Product.select()
        
        products_list = []
        for product in products:
            products_list.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price / 100,  # Convert from cents to dollars
                'in_stock': product.in_stock,
                'weight': product.weight,
                'image': product.image
            })
        
        return jsonify({'products': products_list})
    finally:
        if not db.is_closed():
            db.close()

@bp.route('/order', methods=['POST'])
def create_order():
    """Create a new order"""
    if not db.is_connection_usable():
        db.connect()
    
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError([{
                'field': 'product',
                'code': 'missing-fields',
                'name': 'La création d\'une commande nécessite un produit'
            }])
        
        # Validate input
        errors = validate_order_creation(data)
        if errors:
            raise ValidationError(errors)
        
        product_data = data['product']
        product_id = product_data['id']
        quantity = product_data['quantity']
        
        # Check if product exists and is in stock
        product = Product.get_by_id(product_id)
        if not product.in_stock:
            raise ValidationError([{
                'field': 'product',
                'code': 'out-of-inventory',
                'name': 'Le produit demandé n\'est pas en inventaire'
            }])
        
        # Create order
        order = OrderService.create_order(product_id, quantity)
        
        # Return 302 with location header
        response = jsonify({})
        response.status_code = 302
        response.headers['Location'] = url_for('api.get_order', order_id=order.id)
        return response
            
    except Product.DoesNotExist:
        raise ValidationError([{
            'field': 'product',
            'code': 'missing-fields',
            'name': 'La création d\'une commande nécessite un produit'
        }])
    except ValueError as e:
        if "out of inventory" in str(e):
            raise ValidationError([{
                'field': 'product',
                'code': 'out-of-inventory',
                'name': 'Le produit demandé n\'est pas en inventaire'
            }])
        else:
            raise ValidationError([{
                'field': 'product',
                'code': 'missing-fields',
                'name': 'La création d\'une commande nécessite un produit'
            }])
    finally:
        if not db.is_closed():
            db.close()

@bp.route('/order/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order by ID"""
    if not db.is_connection_usable():
        db.connect()
    
    try:
        order = OrderService.get_order(order_id)
        if not order:
            raise NotFoundError("Order not found")
        
        return jsonify(format_order_response(order))
    finally:
        if not db.is_closed():
            db.close()

@bp.route('/order/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """Update order with customer information or process payment"""
    if not db.is_connection_usable():
        db.connect()
    
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError([{
                'field': 'order',
                'code': 'missing-fields',
                'name': 'Il manque un ou plusieurs champs qui sont obligatoires'
            }])
        
        order = OrderService.get_order(order_id)
        if not order:
            raise NotFoundError("Order not found")
        
        # Check if this is a payment request (credit_card present)
        if 'credit_card' in data:
            # Payment request
            if order.paid:
                raise ValidationError([{
                    'field': 'order',
                    'code': 'already-paid',
                    'name': 'La commande a déjà été payée.'
                }])
            
            if not order.email or not order.shipping_information:
                raise ValidationError([{
                    'field': 'order',
                    'code': 'missing-fields',
                    'name': 'Les informations du client sont nécessaire avant d\'appliquer une carte de crédit'
                }])
            
            # Validate payment data
            errors = validate_payment_data(data)
            if errors:
                raise ValidationError(errors)
            
            try:
                order = OrderService.process_payment(order_id, data['credit_card'])
                return jsonify(format_order_response(order))
            except ValueError as e:
                error_msg = str(e)
                if "card-declined" in error_msg or "incorrect-number" in error_msg:
                    # Parse payment service error
                    import json
                    try:
                        error_data = json.loads(error_msg)
                        return jsonify(error_data), 422
                    except:
                        pass
                
                raise ValidationError([{
                    'field': 'credit_card',
                    'code': 'card-declined',
                    'name': 'La carte de crédit a été déclinée.'
                }])
        
        elif 'order' in data:
            # Customer information update request
            # Validate that no credit_card is present with order info
            if 'credit_card' in data:
                raise ValidationError([{
                    'field': 'order',
                    'code': 'missing-fields',
                    'name': 'Les informations de client et de paiement doivent être envoyées séparément'
                }])
            
            # Validate order update data
            errors = validate_order_update(data)
            if errors:
                raise ValidationError(errors)
            
            order_data = data['order']
            email = order_data['email']
            shipping_info = order_data['shipping_information']
            
            try:
                order = OrderService.update_order_info(order_id, email, shipping_info)
                return jsonify(format_order_response(order))
            except ValueError as e:
                raise ValidationError([{
                    'field': 'order',
                    'code': 'missing-fields',
                    'name': str(e)
                }])
        
        else:
            raise ValidationError([{
                'field': 'order',
                'code': 'missing-fields',
                'name': 'Il manque un ou plusieurs champs qui sont obligatoires'
            }])
    finally:
        if not db.is_closed():
            db.close()

# Error handlers
@bp.errorhandler(ValidationError)
def handle_validation_exception(e):
    return handle_validation_error(e)

@bp.errorhandler(NotFoundError)
def handle_not_found_exception(e):
    return handle_not_found_error(e)

@bp.errorhandler(BusinessError)
def handle_business_exception(e):
    response = jsonify({'errors': {'order': {'code': e.code, 'name': e.message}}})
    response.status_code = e.status_code
    return response

@bp.errorhandler(Exception)
def handle_general_exception(e):
    return handle_api_error(BusinessError("Internal server error", "internal-error", 500))
