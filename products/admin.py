from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Product, Category, ProductScreenshot

# Inline cho Screenshots
class ProductScreenshotInline(admin.TabularInline):
    model = ProductScreenshot
    extra = 1
    verbose_name = _('Screenshot')
    verbose_name_plural = _('Screenshots')

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
        'created_at'
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
        'supported_platforms'
    )
    
    # Tạo slug tự động
    prepopulated_fields = {'slug': ('name',)}
    
    # Thêm inline screenshots
    inlines = [ProductScreenshotInline]
    
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
                'demo_url', 
                'download_url'
            )
        }),
        (_('Additional Information'), {
            'fields': (
                'download_count', 
                'release_date'
            )
        })
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ProductScreenshot)
class ProductScreenshotAdmin(admin.ModelAdmin):
    list_display = ('product', 'caption', 'order')
    list_filter = ('product',)