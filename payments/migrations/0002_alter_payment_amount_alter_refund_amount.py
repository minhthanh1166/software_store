# Generated by Django 5.2 on 2025-04-13 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
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
