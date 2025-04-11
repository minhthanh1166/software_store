from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from orders.models import Order

class Payment(models.Model):
    PAYMENT_METHODS = (
        ('credit_card', _('Credit Card')),
        ('paypal', _('PayPal')),
        ('bank_transfer', _('Bank Transfer')),
        ('crypto', _('Cryptocurrency')),
    )

    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    payment_method = models.CharField(_('payment method'), max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(_('transaction id'), max_length=100, unique=True)
    payment_details = models.JSONField(_('payment details'), blank=True, null=True)
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment #{self.id} - {self.order}"

class Refund(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('completed', _('Completed')),
    )

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    reason = models.TextField(_('reason'))
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(_('admin notes'), blank=True)
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('refund')
        verbose_name_plural = _('refunds')
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund #{self.id} - {self.payment}"
