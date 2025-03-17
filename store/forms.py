from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    shipping_address = forms.CharField(max_length=255, required=True, label="Dirección")
    phone_number = forms.CharField(max_length=20, required=True, label="Teléfono")

    class Meta:
        model = User
        fields = ('username', 'email', 'shipping_address', 'phone_number', 'password1', 'password2')
