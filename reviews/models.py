from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from products.models import Product

class Review(models.Model):
    RATING_CHOICES = (
        (1, _('1 Star')),
        (2, _('2 Stars')),
        (3, _('3 Stars')),
        (4, _('4 Stars')),
        (5, _('5 Stars')),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(
        _('rating'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(_('title'), max_length=200)
    content = models.TextField(_('content'))
    is_verified_purchase = models.BooleanField(_('verified purchase'), default=False)
    helpful_votes = models.PositiveIntegerField(_('helpful votes'), default=0)
    is_approved = models.BooleanField(_('is approved'), default=False)
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        ordering = ['-created_at']
        unique_together = ['product', 'user']

    def __str__(self):
        return f"{self.user.email}'s review for {self.product.name}"

class ReviewResponse(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_responses')
    content = models.TextField(_('content'))
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('review response')
        verbose_name_plural = _('review responses')
        ordering = ['created_at']

    def __str__(self):
        return f"Response to {self.review}"
