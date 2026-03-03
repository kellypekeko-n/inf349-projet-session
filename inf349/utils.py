from decimal import Decimal

def calculate_shipping_price(total_weight_grams):
    """Calculate shipping price based on total weight"""
    if total_weight_grams <= 500:
        return 500  # 5$ in cents
    elif total_weight_grams <= 2000:
        return 1000  # 10$ in cents
    else:
        return 2500  # 25$ in cents

def calculate_tax(amount_cents, province):
    """Calculate tax based on province"""
    tax_rates = {
        'QC': Decimal('0.15'),
        'ON': Decimal('0.13'),
        'AB': Decimal('0.05'),
        'BC': Decimal('0.12'),
        'NS': Decimal('0.14')
    }
    
    rate = tax_rates.get(province, Decimal('0.15'))  # Default to QC rate
    return Decimal(amount_cents) * rate

def validate_order_creation(data):
    """Validate order creation data"""
    errors = []
    
    if not data.get('product'):
        errors.append({
            'field': 'product',
            'code': 'missing-fields',
            'name': 'La création d\'une commande nécessite un produit'
        })
        return errors
    
    product = data['product']
    
    if not isinstance(product, dict):
        errors.append({
            'field': 'product',
            'code': 'missing-fields',
            'name': 'La création d\'une commande nécessite un produit'
        })
        return errors
    
    if 'id' not in product or 'quantity' not in product:
        errors.append({
            'field': 'product',
            'code': 'missing-fields',
            'name': 'La création d\'une commande nécessite un produit'
        })
    
    if 'quantity' in product and product['quantity'] < 1:
        errors.append({
            'field': 'product',
            'code': 'missing-fields',
            'name': 'La création d\'une commande nécessite un produit'
        })
    
    return errors

def validate_order_update(data):
    """Validate order update data"""
    errors = []
    
    if not data.get('order'):
        errors.append({
            'field': 'order',
            'code': 'missing-fields',
            'name': 'Il manque un ou plusieurs champs qui sont obligatoires'
        })
        return errors
    
    order_data = data['order']
    
    # Check for email
    if not order_data.get('email'):
        errors.append({
            'field': 'order',
            'code': 'missing-fields',
            'name': 'Il manque un ou plusieurs champs qui sont obligatoires'
        })
    
    # Check for shipping information
    shipping_info = order_data.get('shipping_information', {})
    required_shipping_fields = ['country', 'address', 'postal_code', 'city', 'province']
    
    for field in required_shipping_fields:
        if not shipping_info.get(field):
            errors.append({
                'field': 'order',
                'code': 'missing-fields',
                'name': 'Il manque un ou plusieurs champs qui sont obligatoires'
            })
            break
    
    return errors

def validate_payment_data(data):
    """Validate payment data"""
    errors = []
    
    if not data.get('credit_card'):
        errors.append({
            'field': 'credit_card',
            'code': 'missing-fields',
            'name': 'Les informations de carte de crédit sont requises'
        })
        return errors
    
    credit_card = data['credit_card']
    required_fields = ['name', 'number', 'expiration_year', 'expiration_month', 'cvv']
    
    for field in required_fields:
        if not credit_card.get(field):
            errors.append({
                'field': 'credit_card',
                'code': 'missing-fields',
                'name': 'Les informations de carte de crédit sont requises'
            })
            break
    
    return errors

def format_order_response(order):
    """Format order data for API response"""
    from decimal import Decimal
    
    response = {
        'order': {
            'id': order.id,
            'total_price': order.total_price,
            'total_price_tax': float(order.total_price_tax) if order.total_price_tax else 0,
            'email': order.email,
            'credit_card': {},
            'shipping_information': {},
            'paid': order.paid,
            'transaction': {},
            'product': {
                'id': order.product.id,
                'quantity': order.quantity
            },
            'shipping_price': order.shipping_price
        }
    }
    
    # Add shipping information if present
    if order.shipping_information:
        response['order']['shipping_information'] = {
            'country': order.shipping_information.country,
            'address': order.shipping_information.address,
            'postal_code': order.shipping_information.postal_code,
            'city': order.shipping_information.city,
            'province': order.shipping_information.province
        }
    
    # Add credit card information if present
    if order.credit_card:
        response['order']['credit_card'] = {
            'name': order.credit_card.name,
            'first_digits': order.credit_card.first_digits,
            'last_digits': order.credit_card.last_digits,
            'expiration_year': order.credit_card.expiration_year,
            'expiration_month': order.credit_card.expiration_month
        }
    
    # Add transaction information if present
    if order.transaction:
        response['order']['transaction'] = {
            'id': order.transaction.id,
            'success': order.transaction.success,
            'amount_charged': order.transaction.amount_charged
        }
    
    return response
