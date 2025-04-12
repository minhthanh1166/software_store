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
    
    # Media
    thumbnail = models.ImageField(_('thumbnail'), upload_to='products/thumbnails/')
    demo_url = models.URLField(_('demo URL'), blank=True)
    download_url = models.URLField(_('download URL'))
    
    # Fields cho việc theo dõi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            total_rating = sum(review.rating for review in reviews)
            return round(total_rating / reviews.count(), 1)
        return 0
    
    @property
    def rating_distribution(self):
        """Tính phân bố điểm đánh giá (số lượng mỗi sao)"""
        distribution = {i: 0 for i in range(1, 6)}
        reviews = self.reviews.filter(is_approved=True)
        
        for review in reviews:
            distribution[review.rating] += 1
            
        return distribution
    
    @property
    def total_reviews(self):
        """Tổng số đánh giá đã được duyệt"""
        return self.reviews.filter(is_approved=True).count()
    slug = models.SlugField(unique=True)
    description = models.TextField(_('description'))
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    software_type = models.CharField(_('software type'), max_length=20, choices=SOFTWARE_TYPES)
    license_type = models.CharField(_('license type'), max_length=20, choices=LICENSE_TYPES)
    version = models.CharField(_('version'), max_length=50)
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    
    # Thông tin kỹ thuật
    system_requirements = models.TextField(_('system requirements'), blank=True)
    supported_platforms = models.CharField(_('supported platforms'), max_length=255)
    file_size = models.CharField(_('file size'), max_length=50)\
    
    demo_url = models.URLField(_('demo URL'), blank=True, null=True)
    download_url = models.URLField(_('download URL'), blank=True, null=True)
    
    # Hình ảnh và media
    thumbnail = models.ImageField(_('thumbnail'), upload_to='products/thumbnails/')
    
    # Thông tin bổ sung
    is_featured = models.BooleanField(_('is featured'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    download_count = models.PositiveIntegerField(_('download count'), default=0)
    
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