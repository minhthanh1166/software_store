from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from accounts.models import User

# Create your models here.
class Category(models.Model):
    """
    Danh mục sản phẩm phần mềm
    """
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(_('description'), blank=True)
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')

    # Fields cho việc theo dõi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    SOFTWARE_TYPES = (
        ('desktop', _('Desktop Application')),
        ('web', _('Web Application')),
        ('mobile', _('Mobile Application')),
        ('plugin', _('Plugin/Extension')),
        ('other', _('Other')),
    )

    LICENSE_TYPES = (
        ('single', _('Single User')),
        ('multi', _('Multi User')),
        ('enterprise', _('Enterprise')),
        ('subscription', _('Subscription')),
    )

    # Thông tin cơ bản
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(_('description'))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='developed_products')
    
    # Thông tin phần mềm
    version = models.CharField(_('version'), max_length=50)
    software_type = models.CharField(_('software type'), max_length=20, choices=SOFTWARE_TYPES)
    license_type = models.CharField(_('license type'), max_length=20, choices=LICENSE_TYPES)
    supported_platforms = models.CharField(_('supported platforms'), max_length=200)
    system_requirements = models.TextField(_('system requirements'), blank=True)
    file_size = models.CharField(_('file size'), max_length=50)
    
    # Giá và trạng thái
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(_('is active'), default=True)
    is_featured = models.BooleanField(_('is featured'), default=False)
    download_count = models.PositiveIntegerField(_('download count'), default=0)
    
    # Media và URLs
    thumbnail = models.ImageField(_('thumbnail'), upload_to='products/thumbnails/')
    demo_url = models.URLField(_('demo URL'), blank=True, null=True)
    download_url = models.URLField(_('download URL'), blank=True, null=True)
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    release_date = models.DateField(_('release date'))
    
    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def average_rating(self):
        """Tính điểm đánh giá trung bình của sản phẩm"""
        reviews = self.product_reviews.filter(is_approved=True)
        if reviews.exists():
            total_rating = sum(review.rating for review in reviews)
            return round(total_rating / reviews.count(), 1)
        return 0
    
    @property
    def rating_distribution(self):
        """Tính phân bố điểm đánh giá (số lượng mỗi sao)"""
        distribution = {i: 0 for i in range(1, 6)}
        reviews = self.product_reviews.filter(is_approved=True)
        
        for review in reviews:
            distribution[review.rating] += 1
            
        return distribution
    
    @property
    def total_reviews(self):
        """Tổng số đánh giá đã được duyệt"""
        return self.product_reviews.filter(is_approved=True).count()

class ProductScreenshot(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField(_('screenshot'), upload_to='products/screenshots/')
    caption = models.CharField(_('caption'), max_length=255, blank=True)
    order = models.PositiveIntegerField(_('order'), default=0)

    class Meta:
        verbose_name = _('product screenshot')
        verbose_name_plural = _('product screenshots')
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - Screenshot {self.order}"

class Review(models.Model):
    """
    Đánh giá sản phẩm của người dùng
    """
    RATING_CHOICES = (
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    title = models.CharField(_('title'), max_length=200)
    content = models.TextField(_('content'))
    is_approved = models.BooleanField(_('is approved'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        ordering = ['-created_at']
        unique_together = ['product', 'user']

    def __str__(self):
        return f"{self.user.username}'s review for {self.product.name}"

class Order(models.Model):
    """
    Đơn hàng
    """
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_orders')
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(_('total amount'), max_digits=10, decimal_places=2)
    payment_method = models.CharField(_('payment method'), max_length=50)
    payment_status = models.BooleanField(_('payment status'), default=False)
    shipping_address = models.TextField(_('shipping address'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    """
    Chi tiết đơn hàng
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class License(models.Model):
    """
    Giấy phép phần mềm
    """
    LICENSE_STATUS = (
        ('active', _('Active')),
        ('expired', _('Expired')),
        ('revoked', _('Revoked')),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='licenses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='licenses')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='licenses')
    license_key = models.CharField(_('license key'), max_length=100, unique=True)
    status = models.CharField(_('status'), max_length=20, choices=LICENSE_STATUS, default='active')
    activation_date = models.DateTimeField(_('activation date'), auto_now_add=True)
    expiry_date = models.DateTimeField(_('expiry date'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('license')
        verbose_name_plural = _('licenses')
        ordering = ['-created_at']

    def __str__(self):
        return f"License for {self.product.name} - {self.user.username}"

class Download(models.Model):
    """
    Theo dõi lượt tải phần mềm
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='downloads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='downloads')
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name='downloads')
    ip_address = models.GenericIPAddressField(_('IP address'))
    user_agent = models.TextField(_('user agent'))
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('download')
        verbose_name_plural = _('downloads')
        ordering = ['-downloaded_at']

    def __str__(self):
        return f"Download of {self.product.name} by {self.user.username}"

class Wishlist(models.Model):
    """
    Danh sách yêu thích của người dùng
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('wishlist')
        verbose_name_plural = _('wishlist')
        ordering = ['-added_at']
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.username}'s wishlist - {self.product.name}"

class Cart(models.Model):
    """
    Giỏ hàng của người dùng
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')
        ordering = ['-created_at']

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_items(self):
        return self.items.count()

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    """
    Chi tiết giỏ hàng
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in cart"

    @property
    def total_price(self):
        return self.product.price * self.quantity

class Payment(models.Model):
    """
    Thông tin thanh toán
    """
    PAYMENT_METHODS = (
        ('credit_card', _('Credit Card')),
        ('paypal', _('PayPal')),
        ('bank_transfer', _('Bank Transfer')),
    )

    PAYMENT_STATUS = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    payment_method = models.CharField(_('payment method'), max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(_('status'), max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(_('transaction ID'), max_length=100, unique=True)
    payment_date = models.DateTimeField(_('payment date'), auto_now_add=True)
    payment_details = models.JSONField(_('payment details'), default=dict)

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment #{self.transaction_id} - {self.amount}"

class Refund(models.Model):
    """
    Yêu cầu hoàn tiền
    """
    REFUND_STATUS = (
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('completed', _('Completed')),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    reason = models.TextField(_('reason'))
    status = models.CharField(_('status'), max_length=20, choices=REFUND_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)

    class Meta:
        verbose_name = _('refund')
        verbose_name_plural = _('refunds')
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund for Order #{self.order.id}"

class Notification(models.Model):
    """
    Thông báo cho người dùng
    """
    NOTIFICATION_TYPES = (
        ('order', _('Order')),
        ('payment', _('Payment')),
        ('license', _('License')),
        ('system', _('System')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(_('type'), max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(_('title'), max_length=200)
    message = models.TextField(_('message'))
    is_read = models.BooleanField(_('is read'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(_('related object ID'), null=True, blank=True)

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Tag(models.Model):
    """
    Thẻ cho sản phẩm
    """
    name = models.CharField(_('name'), max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(_('description'), blank=True)
    products = models.ManyToManyField(Product, related_name='tags', blank=True)

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Version(models.Model):
    """
    Phiên bản phần mềm
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(_('version number'), max_length=50)
    release_notes = models.TextField(_('release notes'))
    download_url = models.URLField(_('download URL'))
    file_size = models.CharField(_('file size'), max_length=50)
    is_active = models.BooleanField(_('is active'), default=True)
    release_date = models.DateTimeField(_('release date'), auto_now_add=True)

    class Meta:
        verbose_name = _('version')
        verbose_name_plural = _('versions')
        ordering = ['-release_date']
        unique_together = ['product', 'version_number']

    def __str__(self):
        return f"{self.product.name} v{self.version_number}"

class FAQ(models.Model):
    """
    Câu hỏi thường gặp
    """
    CATEGORIES = (
        ('general', _('General')),
        ('installation', _('Installation')),
        ('licensing', _('Licensing')),
        ('payment', _('Payment')),
        ('technical', _('Technical Support')),
    )

    question = models.CharField(_('question'), max_length=255)
    answer = models.TextField(_('answer'))
    category = models.CharField(_('category'), max_length=20, choices=CATEGORIES)
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')
        ordering = ['category', 'question']

    def __str__(self):
        return self.question