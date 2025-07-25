import uuid
from lib2to3.fixes.fix_input import context

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import models, transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, TemplateView, DetailView
from rest_framework import status, mixins, generics, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, UpdateAPIView, ListAPIView
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from users.forms import LoginUserForm, RegisterUserForm, ProfileUserForm, MarriageProposalForm
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

    def perform_create(self, serializer):
        sender = self.request.user
        validated_data = serializer.validated_data

        receiver = None
        receiver_fullname = None

        with transaction.atomic():
            if MarriageProposals.objects.filter(sender=sender, status=MarriageProposals.Status.WAITING).exists():
                raise serializers.ValidationError("You have already sent an offer")

            if 'receiver_username' in validated_data:
                # Existing user case
                username = validated_data.pop('receiver_username')
                receiver = User.objects.get(username=username)

                if sender == receiver:
                    raise serializers.ValidationError("You can't send it to yourself")

                if receiver.gender == sender.gender:
                    raise serializers.ValidationError("You can't send to same-sex user")
            else:
                # New user case
                first_name = validated_data.pop('first_name')
                last_name = validated_data.pop('last_name')
                gender = validated_data.pop('gender')
                receiver_fullname = f"{first_name} {last_name}".strip()

                if sender.get_full_name() == receiver_fullname:
                    raise serializers.ValidationError("You can't send it to yourself")

                receiver = User.objects.create(
                    username=f"user_{uuid.uuid4().hex[:8]}",
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    is_active=True
                )

                # For new users, automatically complete the marriage
                validated_data['status'] = MarriageProposals.Status.COMPLETE

            # Create marriage if status is COMPLETE
            if validated_data.get('status') == MarriageProposals.Status.COMPLETE:
                husband, wife = (sender, receiver) if sender.gender == User.Gender.MAN else (receiver, sender)
                User.objects.filter(pk__in=[sender.pk, receiver.pk]).update(is_married=True)
                Marriage.objects.create(husband=husband, wife=wife)

            serializer.save(
                sender=sender,
                receiver=receiver,
                receiver_fullname=receiver_fullname,
                status=validated_data.get('status', MarriageProposals.Status.WAITING)
            )

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            # Возвращаем JSON для JS (можно кастомизировать)
            return Response({"success": True, "message": "Предложение отправлено!"}, status=status.HTTP_201_CREATED)
        return response

class ProposalHTML(TemplateView):
    template_name = 'users/proposal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        proposal_type = self.request.GET.get('type', 'registered')
        is_for_registered = proposal_type != 'unregistered'

        free_users = User.objects.filter(~Q(username=self.request.user.username), is_married=False)

        form = MarriageProposalForm(initial={'type': proposal_type})

        context.update({
            'free_users': free_users,
            'is_for_registered': is_for_registered,
            'form': form,
        })

        return context

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
    mixins.UpdateModelMixin,
    generics.GenericAPIView
):
    def get_object(self):
        user = self.request.user

        marriage = Marriage.objects.filter(
            (models.Q(husband=user) | models.Q(wife=user)),
            status=Marriage.Status.ACTIVE
        ).first()

        if not marriage:
            raise Http404("Вы не состоите в активном браке")
        return marriage

    def update(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                marriage = self.get_object()

                husband = marriage.husband
                wife = marriage.wife
                husband.is_married = False
                wife.is_married = False
                husband.save()
                wife.save()

                marriage.status = Marriage.Status.DIVORCED
                marriage.save()

                return Response(
                    {"detail": "Брак расторгнут успешно"},
                    status=status.HTTP_200_OK
                )

        except Http404:
            return Response(
                {"detail": "Активный брак не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

class MarriagesHTML(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'users/marriages-list.html'

    def get(self, request, *args, **kwargs):
        marriages = Marriage.objects.filter(
            models.Q(husband=request.user) | models.Q(wife=request.user))

        marriages_data = []
        for marriage in marriages.select_related('husband', 'wife'):
            partner = marriage.wife if marriage.husband == request.user else marriage.husband


            marriages_data.append({
                'partner': partner,
                'start_date': marriage.created_at.strftime("%d.%m.%Y"),
                'end_date': marriage.updated_at.strftime("%d.%m.%Y")
                if marriage.status != Marriage.Status.ACTIVE else None,
                'is_active': marriage.status == Marriage.Status.ACTIVE,
                'partner_photo': getattr(partner, 'has_photo', '/media/users/default.png')
            })


        marriages_data.sort(key=lambda x: x['start_date'], reverse=True)

        return Response({
            'marriages_list': marriages_data,
            'request': request
        })
