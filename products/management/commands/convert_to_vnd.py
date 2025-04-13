from django.core.management.base import BaseCommand
from products.models import Product, Order, OrderItem
from payments.models import Payment, Refund
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Converts all currency values to VND (integer values)'

    def handle(self, *args, **options):
        self.stdout.write('Starting currency conversion to VND...')
        
        # Convert Product prices
        count = 0
        for product in Product.objects.all():
            try:
                old_value = product.price
                product.price = Decimal(int(product.price))
                product.save()
                count += 1
                self.stdout.write(f'  Updated product {product.id}: {old_value} -> {product.price}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error updating product {product.id}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Updated {count} product prices'))
        
        # Convert Order amounts
        count = 0
        for order in Order.objects.all():
            try:
                old_value = order.total_amount
                order.total_amount = Decimal(int(order.total_amount))
                order.save()
                count += 1
                self.stdout.write(f'  Updated order {order.id}: {old_value} -> {order.total_amount}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error updating order {order.id}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Updated {count} order amounts'))
        
        # Convert OrderItem prices
        count = 0
        for item in OrderItem.objects.all():
            try:
                old_value = item.price
                item.price = Decimal(int(item.price))
                item.save()
                count += 1
                self.stdout.write(f'  Updated order item {item.id}: {old_value} -> {item.price}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error updating order item {item.id}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Updated {count} order item prices'))
        
        # Convert Payment amounts
        count = 0
        for payment in Payment.objects.all():
            try:
                old_value = payment.amount
                payment.amount = Decimal(int(payment.amount))
                payment.save()
                count += 1
                self.stdout.write(f'  Updated payment {payment.id}: {old_value} -> {payment.amount}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error updating payment {payment.id}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Updated {count} payment amounts'))
        
        # Convert Refund amounts
        count = 0
        for refund in Refund.objects.all():
            try:
                old_value = refund.amount
                refund.amount = Decimal(int(refund.amount))
                refund.save()
                count += 1
                self.stdout.write(f'  Updated refund {refund.id}: {old_value} -> {refund.amount}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error updating refund {refund.id}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Updated {count} refund amounts'))
        
        self.stdout.write(self.style.SUCCESS('Currency conversion to VND completed')) 