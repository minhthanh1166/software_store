from django.db import migrations, models
from django.core.validators import MinValueValidator
import math

def round_currency_values(apps, schema_editor):
    # Update Product prices
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.all():
        product.price = round(product.price)
        product.save()
    
    # Update Order amounts
    Order = apps.get_model('products', 'Order')
    for order in Order.objects.all():
        order.total_amount = round(order.total_amount)
        order.save()
    
    # Update OrderItem prices
    OrderItem = apps.get_model('products', 'OrderItem')
    for item in OrderItem.objects.all():
        item.price = round(item.price)
        item.save()

class Migration(migrations.Migration):
    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        # First round all values to integers for VND
        migrations.RunPython(round_currency_values),
        
        # Then update the field definitions
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=0, max_digits=12, validators=[MinValueValidator(0)], verbose_name='price'),
        ),
        
        migrations.AlterField(
            model_name='order',
            name='total_amount',
            field=models.DecimalField(decimal_places=0, max_digits=12, verbose_name='total amount'),
        ),
        
        migrations.AlterField(
            model_name='orderitem',
            name='price',
            field=models.DecimalField(decimal_places=0, max_digits=12, verbose_name='price'),
        ),
    ] 