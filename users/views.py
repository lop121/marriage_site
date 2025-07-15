from django.contrib.auth.views import LoginView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from users.forms import LoginUserForm, RegisterUserForm
from users.models import User


class HomePage(ListView):
    template_name = 'users/index.html'
    extra_context = {
        'title': 'HomePage'
    }

    def get_queryset(self):
        return User.married.all()

class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': 'Log In'}

class RegistrationUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': 'Registration'}
    success_url = reverse_lazy('login')

class UserProfile(UpdateView):
    pass
