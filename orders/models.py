from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from accounts.models import User
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(_('total amount'), max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_status = models.BooleanField(_('payment status'), default=False)
    payment_method = models.CharField(_('payment method'), max_length=50, blank=True)
    transaction_id = models.CharField(_('transaction id'), max_length=100, blank=True)
    
    # Thông tin giao hàng
    shipping_address = models.TextField(_('shipping address'))
    shipping_phone = models.CharField(_('shipping phone'), max_length=15)
    shipping_email = models.EmailField(_('shipping email'))
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.user.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    license_key = models.CharField(_('license key'), max_length=100, blank=True)
    download_url = models.URLField(_('download url'), blank=True)
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        return self.price * self.quantity
