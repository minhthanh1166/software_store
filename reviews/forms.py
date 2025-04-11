from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Review, ReviewResponse

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'content']
        widgets = {
            'rating': forms.RadioSelect(choices=Review.RATING_CHOICES),
            'title': forms.TextInput(attrs={'placeholder': _('Enter a title for your review')}),
            'content': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': _('Share your experience with this product')
            }),
        }

class ReviewResponseForm(forms.ModelForm):
    class Meta:
        model = ReviewResponse
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': _('Write your response here')
            }),
        } 