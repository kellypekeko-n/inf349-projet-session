import requests
from decimal import Decimal
from .models import Product, Order, ShippingInformation, CreditCard, Transaction
from .utils import calculate_shipping_price, calculate_tax
from . import db

class ProductService:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def fetch_products(self):
        """Fetch products from remote service and store them locally"""
        try:
            response = requests.get(f"{self.base_url}products.json")
            response.raise_for_status()
            data = response.json()
            
            products = []
            for product_data in data.get('products', []):
                product, created = Product.get_or_create(
                    id=product_data['id'],
                    defaults={
                        'name': product_data['name'],
                        'description': product_data['description'],
                        'price': int(product_data['price'] * 100),  # Convert to cents
                        'in_stock': product_data['in_stock'],
                        'weight': product_data['weight'],
                        'image': product_data['image']
                    }
                )
                if created:
                    products.append(product)
                else:
                    # Update existing product
                    product.name = product_data['name']
                    product.description = product_data['description']
                    product.price = int(product_data['price'] * 100)
                    product.in_stock = product_data['in_stock']
                    product.weight = product_data['weight']
                    product.image = product_data['image']
                    product.save()
                    products.append(product)
            
            return products
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch products: {str(e)}")

class OrderService:
    @staticmethod
    def create_order(product_id, quantity):
        """Create a new order"""
        if not db.is_connection_usable():
            db.connect()
        
        try:
            if quantity < 1:
                raise ValueError("Quantity must be >= 1")
            
            try:
                product = Product.get_by_id(product_id)
            except Product.DoesNotExist:
                raise ValueError("Product not found")
            
            if not product.in_stock:
                raise ValueError("Product out of inventory")
            
            total_price = product.price * quantity
            shipping_price = calculate_shipping_price(product.weight * quantity)
            
            # Calculate tax (default to QC rate if no shipping info yet)
            total_amount = total_price + shipping_price
            tax_amount = calculate_tax(total_amount, 'QC')  # Default QC rate
            total_price_tax = total_amount + tax_amount
            
            order = Order.create(
                product=product,
                quantity=quantity,
                total_price=total_price,
                shipping_price=shipping_price,
                total_price_tax=total_price_tax
            )
            
            return order
        finally:
            if not db.is_closed():
                db.close()
    
    @staticmethod
    def get_order(order_id):
        """Get order by ID"""
        if not db.is_connection_usable():
            db.connect()
        
        try:
            try:
                return Order.get_by_id(order_id)
            except Order.DoesNotExist:
                return None
        finally:
            if not db.is_closed():
                db.close()
    
    @staticmethod
    def update_order_info(order_id, email, shipping_info):
        """Update order with customer information"""
        if not db.is_connection_usable():
            db.connect()
        
        try:
            order = OrderService.get_order(order_id)
            if not order:
                raise ValueError("Order not found")
            
            if order.paid:
                raise ValueError("Cannot update paid order")
            
            # Create shipping information
            shipping = ShippingInformation.create(
                country=shipping_info['country'],
                address=shipping_info['address'],
                postal_code=shipping_info['postal_code'],
                city=shipping_info['city'],
                province=shipping_info['province']
            )
            
            # Recalculate tax based on new province
            total_amount = order.total_price + order.shipping_price
            tax_amount = calculate_tax(total_amount, shipping_info['province'])
            total_price_tax = total_amount + tax_amount
            
            # Update order
            order.email = email
            order.shipping_information = shipping
            order.total_price_tax = total_price_tax
            order.save()
            
            return order
        finally:
            if not db.is_closed():
                db.close()
    
    @staticmethod
    def process_payment(order_id, credit_card_info):
        """Process payment for an order"""
        order = OrderService.get_order(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.paid:
            raise ValueError("Order already paid")
        
        if not order.email or not order.shipping_information:
            raise ValueError("Customer information required before payment")
        
        # Calculate total amount with tax
        total_amount = order.total_price + order.shipping_price
        tax_amount = calculate_tax(total_amount, order.shipping_information.province)
        final_amount = total_amount + tax_amount
        
        # Process payment through external service
        payment_service = PaymentService("http://dimensweb.uqac.ca/~jgnault/shops/pay/")
        payment_result = payment_service.process_payment(credit_card_info, int(final_amount))
        
        if payment_result['success']:
            # Save credit card info (masked)
            credit_card = CreditCard.create(
                name=credit_card_info['name'],
                first_digits=payment_result['credit_card']['first_digits'],
                last_digits=payment_result['credit_card']['last_digits'],
                expiration_year=credit_card_info['expiration_year'],
                expiration_month=credit_card_info['expiration_month']
            )
            
            # Save transaction info
            transaction = Transaction.create(
                id=payment_result['transaction']['id'],
                success=payment_result['transaction']['success'],
                amount_charged=payment_result['transaction']['amount_charged']
            )
            
            # Update order
            order.credit_card = credit_card
            order.transaction = transaction
            order.paid = True
            order.save()
            
            return order
        else:
            raise ValueError(payment_result.get('error', 'Payment failed'))

class PaymentService:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def process_payment(self, credit_card_info, amount):
        """Process payment through external service"""
        try:
            payload = {
                'credit_card': credit_card_info,
                'amount_charged': amount
            }
            
            response = requests.post(f"{self.base_url}", json=payload)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'credit_card': response.json()['credit_card'],
                    'transaction': response.json()['transaction']
                }
            elif response.status_code == 422:
                error_data = response.json()
                return {
                    'success': False,
                    'error': error_data
                }
            else:
                return {
                    'success': False,
                    'error': 'Payment service error'
                }
                
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Payment service unavailable: {str(e)}'
            }
