from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
import json
from cart.models import Cart, CartItem
from products.models import Product
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrates cart data from sessions to database'

    def handle(self, *args, **options):
        self.stdout.write('Starting cart data migration...')
        
        # Get all active sessions
        active_sessions = Session.objects.all()
        session_count = active_sessions.count()
        migrated_count = 0
        
        self.stdout.write(f'Found {session_count} sessions')
        
        # Process each session
        for session in active_sessions:
            try:
                # Get session data
                session_data = session.get_decoded()
                
                # Check if there's a cart in the session
                if 'cart' in session_data:
                    cart_data = session_data['cart']
                    if not cart_data:
                        continue
                    
                    # Check if there's a user associated with this session
                    if '_auth_user_id' in session_data:
                        user_id = session_data['_auth_user_id']
                        try:
                            user = User.objects.get(pk=user_id)
                            
                            # Create or get the user's cart
                            cart, created = Cart.objects.get_or_create(user=user)
                            
                            # Add each product from the session cart to the database cart
                            for product_id, quantity in cart_data.items():
                                try:
                                    product = Product.objects.get(pk=product_id)
                                    
                                    # Create cart item (only if not exists)
                                    CartItem.objects.get_or_create(
                                        cart=cart,
                                        product=product
                                    )
                                    
                                except Product.DoesNotExist:
                                    self.stdout.write(f'    Product {product_id} not found')
                                    continue
                            
                            migrated_count += 1
                            self.stdout.write(f'  Migrated cart for user {user.username}')
                            
                        except User.DoesNotExist:
                            self.stdout.write(f'  User {user_id} not found')
                            continue
            
            except Exception as e:
                self.stdout.write(f'Error processing session: {str(e)}')
                continue
        
        self.stdout.write(self.style.SUCCESS(f'Successfully migrated {migrated_count} carts')) 