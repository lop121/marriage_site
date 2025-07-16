from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from rest_framework.generics import UpdateAPIView, CreateAPIView, ListCreateAPIView
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.views import APIView

from users.forms import LoginUserForm, RegisterUserForm
from users.models import User, Marriage
from users.serializers import MarriageSerializers


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

class ProposalAPI(ListCreateAPIView):
    queryset = Marriage.objects.all()
    serializer_class = MarriageSerializers

class ProposalHTML(ProposalAPI):
    # renderer_classes = [TemplateHTMLRenderer]
    # template_name = 'users/index.html'
    pass
