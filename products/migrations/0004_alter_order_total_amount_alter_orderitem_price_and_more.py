# Generated by Django 5.2 on 2025-04-13 14:57

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_faq_alter_product_developer_and_more'),
    ]

    operations = [
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
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(decimal_places=0, max_digits=12, verbose_name='amount'),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)], verbose_name='price'),
        ),
        migrations.AlterField(
            model_name='refund',
            name='amount',
            field=models.DecimalField(decimal_places=0, max_digits=12, verbose_name='amount'),
        ),
    ]
