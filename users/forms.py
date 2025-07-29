from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.forms import Select

from users.models import User


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={"autofocus": True}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

class RegisterUserForm(UserCreationForm):

    username = forms.CharField(label='Логин')
    email = forms.EmailField(
        label='Почта',
        widget=forms.EmailInput(attrs={'placeholder': 'user@example.com'})
    )
    first_name = forms.CharField(max_length=150, required=True, label='Имя')
    last_name = forms.CharField(max_length=150, required=True, label='Фамилия')

    password_attrs = {'autocomplete': 'new-password', 'class': 'form-control'}
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(password_attrs))
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput(password_attrs))

    gender = forms.ChoiceField(
        label='Пол',
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
    username = forms.CharField(label='Логин',
                               widget=forms.TextInput(attrs={'class': 'form-input'}), disabled=True)
    email = forms.CharField(label='Почта',
                            widget=forms.TextInput(attrs={'class': 'form-input'}), disabled=True)
    gender = forms.ChoiceField(choices=User.Gender.choices,label='Пол')

    class Meta:
        model = get_user_model()
        fields = ['photo','username', 'email', 'first_name', 'last_name', 'gender']

class MarriageProposalForm(forms.Form):
    type = forms.CharField(widget=forms.HiddenInput(),
                           required=False)
    receiver_username = forms.CharField(required=False, label="Логин")
    first_name = forms.CharField(required=False, label="Имя")
    last_name = forms.CharField(required=False, label="Фамилия")

    gender_choices = [('', 'Выберите пол')] + list(User.Gender.choices)
    gender = forms.ChoiceField(choices=gender_choices, required=False, label="Пол")

    photo = forms.ImageField(required=False, label='Фото')

