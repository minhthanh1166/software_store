from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.cache import cache
from django.utils import timezone
from accounts.models import User
from products.models import Product
from decimal import Decimal
import uuid

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Chờ thanh toán')),
        ('processing', _('Đang xử lý')),
        ('completed', _('Hoàn thành')),
        ('cancelled', _('Đã hủy')),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', _('Chờ thanh toán')),
        ('processing', _('Đang xử lý')),
        ('completed', _('Hoàn thành')),
        ('failed', _('Thất bại')),
    )

    PAYMENT_METHOD_CHOICES = (
        ('sepay', 'SePay'),
        ('bank', _('Chuyển khoản ngân hàng')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', db_index=True)
    status = models.CharField(_('Trạng thái'), max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    payment_status = models.CharField(_('Trạng thái thanh toán'), max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(_('Tổng tiền'), max_digits=10, decimal_places=2, 
                                     validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(_('Phương thức thanh toán'), max_length=20, choices=PAYMENT_METHOD_CHOICES, default='sepay')
    transaction_id = models.CharField(_('Mã giao dịch'), max_length=100, blank=True, null=True)
    transaction_reference = models.CharField(max_length=100, blank=True, null=True, help_text=_('Mã tham chiếu UUID cho giao dịch'))
    
    # Trong cơ sở dữ liệu cũ, vẫn có các trường shipping
    shipping_address = models.CharField(_('Địa chỉ giao hàng'), max_length=255, blank=True, null=True)
    shipping_phone = models.CharField(_('Số điện thoại giao hàng'), max_length=20, blank=True, null=True)
    shipping_email = models.EmailField(_('Email giao hàng'), blank=True, null=True)
    
    # Thời gian
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)
    completed_at = models.DateTimeField(_('Ngày hoàn thành'), null=True, blank=True)

    class Meta:
        verbose_name = _('đơn hàng')
        verbose_name_plural = _('đơn hàng')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', 'created_at']),
        ]

    def __str__(self):
        return f"Đơn hàng #{self.id} - {self.user.email}"

    def save(self, *args, **kwargs):
        # Cập nhật completed_at khi đơn hàng hoàn thành
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        # Xóa cache khi lưu đơn hàng
        cache_keys = [
            f'order_{self.id}',
            f'user_orders_{self.user.id}',
            f'user_completed_orders_{self.user.id}'
        ]
        cache.delete_many(cache_keys)
        
        super().save(*args, **kwargs)

    def get_items_count(self):
        """Lấy tổng số lượng sản phẩm trong đơn hàng"""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def is_pending(self):
        """Kiểm tra đơn hàng đang chờ thanh toán"""
        return self.status == 'pending'

    @property
    def is_completed(self):
        """Kiểm tra đơn hàng đã hoàn thành"""
        return self.status == 'completed'

    @property
    def can_cancel(self):
        """Kiểm tra có thể hủy đơn hàng không"""
        return self.status == 'pending'

    @property
    def payment_status_display_class(self):
        status_classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'processing': 'bg-blue-100 text-blue-800',
            'completed': 'bg-green-100 text-green-800',
            'failed': 'bg-red-100 text-red-800',
        }
        return status_classes.get(self.payment_status, 'bg-gray-100 text-gray-800')

    @property
    def status_display_class(self):
        status_classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'processing': 'bg-blue-100 text-blue-800',
            'completed': 'bg-green-100 text-green-800',
            'cancelled': 'bg-red-100 text-red-800',
        }
        return status_classes.get(self.status, 'bg-gray-100 text-gray-800')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(_('Số lượng'), default=1,
                                         validators=[MinValueValidator(1)])
    price = models.DecimalField(_('Giá'), max_digits=10, decimal_places=2,
                              validators=[MinValueValidator(Decimal('0.01'))])
    license_key = models.CharField(_('License key'), max_length=100, blank=True, null=True)
    download_url = models.URLField(_('URL tải xuống'), blank=True)
    
    # Thời gian
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('sản phẩm trong đơn hàng')
        verbose_name_plural = _('sản phẩm trong đơn hàng')
        indexes = [
            models.Index(fields=['order', 'product']),
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        if not self.license_key and self.order.is_completed:
            self.generate_license_key()
        super().save(*args, **kwargs)

    def generate_license_key(self):
        """Tạo license key mới"""
        self.license_key = f"SW-{self.order.id}-{self.product.id}-{uuid.uuid4().hex[:8].upper()}"

    @property
    def total_price(self):
        return self.price * self.quantity
