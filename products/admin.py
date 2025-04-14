from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Product, Category, ProductScreenshot, FAQ, Wishlist

# Inline cho Screenshots
class ProductScreenshotInline(admin.TabularInline):
    model = ProductScreenshot
    extra = 1
    verbose_name = _('Screenshot')
    verbose_name_plural = _('Screenshots')

class FAQInline(admin.TabularInline):
    model = FAQ
    extra = 1
    fields = ['question', 'answer', 'category', 'is_active']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Các trường hiển thị trong danh sách sản phẩm
    list_display = (
        'name', 
        'category', 
        'software_type', 
        'license_type', 
        'price', 
        'is_active', 
        'created_at',
        'average_rating',
        'total_reviews'
    )
    
    # Các trường để lọc
    list_filter = (
        'is_active', 
        'software_type', 
        'license_type', 
        'category',
        'created_at'
    )
    
    # Các trường để tìm kiếm
    search_fields = (
        'name', 
        'description', 
        'version',
        'supported_platforms',
        'developer__username'
    )
    
    # Tạo slug tự động
    prepopulated_fields = {'slug': ('name',)}
    
    # Thêm inline screenshots
    inlines = [ProductScreenshotInline, FAQInline]
    
    # Các nhóm trường để hiển thị
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name', 
                'slug', 
                'description', 
                'category', 
                'developer'
            )
        }),
        (_('Software Details'), {
            'fields': (
                'version', 
                'software_type', 
                'license_type', 
                'supported_platforms', 
                'system_requirements',
                'file_size'
            )
        }),
        (_('Pricing and Status'), {
            'fields': (
                'price', 
                'is_active', 
                'is_featured'
            )
        }),
        (_('Media and Links'), {
            'fields': (
                'thumbnail', 
                'thumbnail_tag',
                'demo_url', 
                'download_url'
            )
        }),
        (_('Additional Information'), {
            'fields': (
                'download_count', 
                'release_date'
            )
        }),
        (_('Ratings'), {
            'fields': (
                'average_rating',
                'total_reviews'
            )
        })
    )

    readonly_fields = ['thumbnail_tag', 'average_rating', 'total_reviews']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at', 'is_active')
    list_filter = ('created_at', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['image_tag']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name', 
                'slug', 
                'description', 
                'parent',
                'is_active'
            )
        }),
        (_('Media'), {
            'fields': (
                'icon',
                'image_tag'
            )
        })
    )

@admin.register(ProductScreenshot)
class ProductScreenshotAdmin(admin.ModelAdmin):
    list_display = ('product', 'caption', 'order')
    list_filter = ('product',)

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'product__name']

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'product', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer', 'product__name']