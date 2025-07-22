from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import models, transaction
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView
from rest_framework import status, mixins, generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, UpdateAPIView
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from users.forms import LoginUserForm, RegisterUserForm, ProfileUserForm
from users.models import User, Marriage, MarriageProposals
from users.serializers import MarriageSerializers, OffersSerializers


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

class UserProfile(LoginRequiredMixin,UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_married'] = user.is_married
        context['partner_name'] = user.partner
        return context

    def get_success_url(self):
        return reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

class ProposalAPI(ListCreateAPIView):
    queryset = MarriageProposals.objects.all()
    serializer_class = MarriageSerializers

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if (request.accepted_renderer.format == 'html' and
                response.status_code == status.HTTP_201_CREATED):
            proposal_type = request.GET.get('type', 'registered') or request.POST.get('type', 'registered')
            return redirect(f"{reverse('proposal')}?type={proposal_type}")
        return response

class ProposalHTML(ProposalAPI):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'users/proposal.html'


    def get(self, request, *args, **kwargs):
        is_for_registered = request.GET.get('type') != 'unregistered'
        return Response({
            'proposals': self.get_queryset(),
            'is_for_registered': is_for_registered,
            'request': request
        })

class OffersAPI(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    generics.GenericAPIView
):

    serializer_class = OffersSerializers

    def get_queryset(self):
        return MarriageProposals.objects.filter(
            receiver=self.request.user,
            status=MarriageProposals.Status.WAITING)

    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        if serializer.instance.receiver != self.request.user:
            raise PermissionDenied("You don't update this offer!")
        serializer.save()

class OffersHTML(OffersAPI):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'users/offers.html'


    def get(self, request, *args, **kwargs):
        return Response({
            'offers': self.get_queryset(),
            'request': request
        })

class DivorceAPI(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    generics.GenericAPIView
):

    def get_object(self):
        user = self.request.user

        marriage = Marriage.objects.filter(
            models.Q(husband=user) | models.Q(wife=user)
        ).first()

        if not marriage:
            raise Http404("Вы не состоите в браке")
        return marriage

    def destroy(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                marriage = self.get_object()

                husband = marriage.husband
                wife = marriage.wife

                husband.is_married = False
                wife.is_married = False

                husband.save()
                wife.save()

                marriage.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)

        except Http404:
            return Response(
                {"detail": "Брак не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

# class DivorceHTML(DivorceAPI):
#     renderer_classes = [TemplateHTMLRenderer]
#     template_name = 'users/divorce_confirm.html'

