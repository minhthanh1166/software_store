from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Category, Product, ProductScreenshot, Review

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon', 'parent']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'category', 'software_type',
            'license_type', 'version', 'system_requirements', 'supported_platforms',
            'file_size', 'thumbnail', 'is_featured', 'is_active', 'release_date'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'system_requirements': forms.Textarea(attrs={'rows': 4}),
            'release_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ProductScreenshotForm(forms.ModelForm):
    class Meta:
        model = ProductScreenshot
        fields = ['image', 'caption', 'order']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': _('Enter caption...')}),
            'order': forms.NumberInput(attrs={'min': 0}),
        }

class ProductSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search products...'),
            'class': 'form-control'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label=_('All Categories')
    )
    software_type = forms.ChoiceField(
        choices=Product.SOFTWARE_TYPES,
        required=False,
        # empty_label=_('All Types')
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': _('Min price')})
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': _('Max price')})
    )

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'content']
        widgets = {
            'rating': forms.RadioSelect(),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tiêu đề đánh giá'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Nhập nội dung đánh giá'})
        } 