from django.db import models
from django.conf import settings
from products.models import Product
from django.utils.translation import gettext_lazy as _

class Cart(models.Model):
    """
    Model for storing user's shopping cart in the database
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopping_cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Cart')
        verbose_name_plural = _('Carts')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Cart {self.id} - {self.user.username}"

    @property
    def total(self):
        return sum(item.product.price for item in self.items.all())

    @property
    def count(self):
        return self.items.count()


class CartItem(models.Model):
    """
    Model for storing items in a user's shopping cart
    Quantity is always 1 as per requirement
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')
        unique_together = ('cart', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.product.name}"

    @property
    def total(self):
        return self.product.price 