# Generated by Django 5.2 on 2025-04-13 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_shipping_address_order_shipping_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='transaction_reference',
            field=models.CharField(blank=True, help_text='Mã tham chiếu UUID cho giao dịch', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('sepay', 'SePay'), ('bank', 'Chuyển khoản ngân hàng')], default='sepay', max_length=20, verbose_name='Phương thức thanh toán'),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_status',
            field=models.CharField(choices=[('pending', 'Chờ thanh toán'), ('processing', 'Đang xử lý'), ('completed', 'Hoàn thành'), ('failed', 'Thất bại')], default='pending', max_length=20, verbose_name='Trạng thái thanh toán'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Chờ thanh toán'), ('processing', 'Đang xử lý'), ('completed', 'Hoàn thành'), ('cancelled', 'Đã hủy')], db_index=True, default='pending', max_length=20, verbose_name='Trạng thái'),
        ),
    ]
