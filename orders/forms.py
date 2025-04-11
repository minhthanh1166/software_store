from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'shipping_address',
            'shipping_phone',
            'shipping_email',
            'payment_method'
        ]
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
            'shipping_phone': forms.TextInput(attrs={'placeholder': _('Enter phone number')}),
            'shipping_email': forms.EmailInput(attrs={'placeholder': _('Enter email address')}),
        }

class CartItemForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1})
    ) 