from datetime import date

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.forms import Select

from users.models import User


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Login', widget=forms.TextInput(attrs={"autofocus": True}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

class RegisterUserForm(UserCreationForm):

    username = forms.CharField(label='Login')
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'user@example.com'})
    )
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    password_attrs = {'autocomplete': 'new-password', 'class': 'form-control'}
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(password_attrs))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(password_attrs))

    gender = forms.ChoiceField(
        label='Gender',
        choices=User.Gender.choices,
        widget=Select
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'gender']

    def clean_email(self):
        email = self.cleaned_data['email']
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("This email has already been registered")
        return email

class ProfileUserForm(forms.ModelForm):
    username = forms.CharField(label='Login',
                               widget=forms.TextInput(attrs={'class': 'form-input'}), disabled=True)
    email = forms.CharField(label='E-mail',
                            widget=forms.TextInput(attrs={'class': 'form-input'}), disabled=True)
    this_year = date.today().year
    data_birth = forms.DateField(widget=forms.SelectDateWidget(years=tuple(range(this_year - 100, this_year - 18))))
    is_married = forms.BooleanField(label='Married', disabled=True)

    class Meta:
        model = get_user_model()
        fields = ['photo','username', 'email', 'first_name', 'last_name', 'data_birth', 'is_married']

