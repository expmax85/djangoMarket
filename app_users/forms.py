from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from .models import Customer


class AuthForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        error_messages = {
            'invalid_login': _("Please enter a correct %(username)s and password. "
                               "Note that both fields may be case-sensitive."),
            'inactive': _("This account is inactive."),
        }


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=40, required=False)
    email = forms.EmailField(max_length=50, required=True)
    city = forms.CharField(max_length=40, localize=True, required=False)
    phone_valid = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message=' '.join([str(_('Phone number must be entered in the format:')), '+999999999',
                                                   str(_('Up to 15 digits allowed.'))]))
    phone = forms.CharField(max_length=17, validators=[phone_valid], required=True)

    class Meta:
        model = User
        fields = [
            'username', 'password1',
            'first_name', 'last_name', 'email',
            'city', 'phone',
        ]


class UpBalanceForm(forms.Form):
    balance = forms.DecimalField(max_digits=20, decimal_places=2, required=True)


class CustomerEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=40, required=False)
    email = forms.EmailField(max_length=50, required=True)

    class Meta:
        model = Customer
        fields = [
            'first_name', 'last_name', 'email', 'city', 'phone',
        ]
