from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView
from rest_framework import status
from rest_framework.generics import UpdateAPIView, CreateAPIView, ListCreateAPIView
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from users.forms import LoginUserForm, RegisterUserForm
from users.models import User, Marriage, MarriageProposals
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
    success_url = 'home'

class RegistrationUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': 'Registration'}
    success_url = reverse_lazy('login')

class UserProfile(UpdateView):
    pass

class ProposalAPI(ListCreateAPIView):
    queryset = MarriageProposals.objects.all()
    serializer_class = MarriageSerializers

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if (request.accepted_renderer.format == 'html' and
                response.status_code == status.HTTP_201_CREATED):
            return redirect(reverse('proposal'))
        return response

class ProposalHTML(ProposalAPI):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'users/proposal.html'


    def get(self, request, *args, **kwargs):
        is_for_registered = request.GET.get('type') != 'unregistered'
        return Response({
            'proposals': self.get_queryset(),
            'is_for_registered': is_for_registered
        })
