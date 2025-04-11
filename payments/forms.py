from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Payment, Refund

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method', 'payment_details']
        widgets = {
            'payment_details': forms.Textarea(attrs={'rows': 3}),
        }

class RefundForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': _('Please explain why you want a refund')
            }),
        }

class ProcessRefundForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            ('approve', _('Approve')),
            ('reject', _('Reject'))
        ],
        widget=forms.RadioSelect
    )
    admin_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _('Add any notes for the customer (optional)')
        })
    ) 