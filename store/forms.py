from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ProductReview


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    shipping_address = forms.CharField(max_length=255, required=True, label="Dirección")
    phone_number = forms.CharField(max_length=20, required=True, label="Teléfono")

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'shipping_address',
            'phone_number',
            'password1',
            'password2',
        )


class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'class': 'form-control'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'style': 'resize: none;'
            }),
        }
