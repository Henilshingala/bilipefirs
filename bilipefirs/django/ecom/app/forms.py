from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Customer

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': 'true', 'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}))

class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': 'true', 'class': 'form-control'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists. Please choose a different one.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already registered. Please use a different email address.")
        return email

class MyPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'mobile', 'pincode', 'house_no', 'street',
                 'landmark', 'city', 'state']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'pattern': '[0-9]{10}'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'id': 'pincode', 'maxlength': '6'}),
            'house_no': forms.TextInput(attrs={'class': 'form-control'}),
            'street': forms.TextInput(attrs={'class': 'form-control'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'id': 'district'}),
            'state': forms.Select(attrs={'class': 'form-control', 'id': 'state'}),
        }

    def __init__(self, *args, **kwargs):
        super(CustomerProfileForm, self).__init__(*args, **kwargs)

        for field_name in self.fields:
            self.fields[field_name].initial = None

    def clean_pincode(self):
        pincode = self.cleaned_data['pincode']

        if not pincode.isdigit() or len(pincode) != 6:
            raise forms.ValidationError("Pincode must be exactly 6 digits and numeric.")

        return pincode


class DiscountCodeForm(forms.Form):
    discount_code = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter discount code',
            'class': 'form-control',
            'pattern': '^[A-Za-z0-9]+$',
            'title': 'Only letters and numbers allowed'
        })
    )

    def clean_discount_code(self):
        code = self.cleaned_data['discount_code']
        return code.strip().upper()
