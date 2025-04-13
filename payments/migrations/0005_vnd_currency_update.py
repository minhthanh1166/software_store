from django.db import migrations, models
import math

def round_currency_values(apps, schema_editor):
    # Update Payment amounts
    Payment = apps.get_model('payments', 'Payment')
    for payment in Payment.objects.all():
        payment.amount = round(payment.amount)
        payment.save()
    
    # Update Refund amounts
    Refund = apps.get_model('payments', 'Refund')
    for refund in Refund.objects.all():
        refund.amount = round(refund.amount)
        refund.save()

class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        # First round all values to integers for VND
        migrations.RunPython(round_currency_values),
        
        # Then update the field definitions
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(decimal_places=0, max_digits=12, verbose_name='amount'),
        ),
        
        migrations.AlterField(
            model_name='refund',
            name='amount',
            field=models.DecimalField(decimal_places=0, max_digits=12, verbose_name='amount'),
        ),
    ] 