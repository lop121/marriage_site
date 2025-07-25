import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from rest_framework import status, mixins, generics, serializers, permissions
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from users.forms import LoginUserForm, RegisterUserForm, ProfileUserForm, MarriageProposalForm
from users.models import User, Marriage, MarriageProposals
from users.serializers import MarriageSerializers, OffersSerializers, DivorceSerializer, UserShortSerializer


class HomePage(ListView):
    template_name = 'users/index.html'
    extra_context = {
        'title': 'Главная страница'
    }

    def get_queryset(self):
        return User.married.all()

class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': 'Авторизация'}
    success_url = 'home'

class RegistrationUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': 'Регистрация'}
    success_url = reverse_lazy('login')

class UserProfile(LoginRequiredMixin,UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user # type: User

        context.update({
            'is_married': user.is_married,
            'partner_name': user.partner,
        })

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
                raise serializers.ValidationError("У тебя уже есть отправленное предложение")

            if 'receiver_username' in validated_data:
                # Existing user case
                username = validated_data.pop('receiver_username')
                receiver = User.objects.get(username=username)

                if sender == receiver:
                    raise serializers.ValidationError("Ты не можешь отправить запрос самому себе")

                if receiver.gender == sender.gender:
                    raise serializers.ValidationError("Однополые браки запрещены!")
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
            )

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            return Response({"success": True, "message": "Предложение отправлено!"}, status=status.HTTP_201_CREATED)
        return response

class UserAutocompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        q = request.GET.get('q', '')  # Получаем поисковую строку из параметра q
        users = User.objects.filter(is_married=False)
        if q:
            users = users.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q)
            )
        users = users[:10]  # Ограничиваем 10 результатами
        serializer = UserShortSerializer(users, many=True)
        return Response(serializer.data)

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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Поступившие заявки
        incoming = MarriageProposals.objects.filter(
            receiver=self.request.user,
            status=MarriageProposals.Status.WAITING
        )
        # Отправленные заявки
        outgoing = MarriageProposals.objects.filter(
            sender=self.request.user,
            status=MarriageProposals.Status.WAITING
        )
        return incoming | outgoing

    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.instance
        validated_data = serializer.validated_data

        user = self.request.user

        # Получатель может принять/отклонить, отправитель — только отменить
        if user != instance.receiver and user != instance.sender:
            raise PermissionDenied("Ты не можешь изменить эту заявку!")

        if user == instance.sender and serializer.validated_data.get('status') != MarriageProposals.Status.CANCELED:
            raise PermissionDenied("Отправитель может только отменить заявку!")

        with transaction.atomic():
            if (instance.status == MarriageProposals.Status.WAITING and
                    validated_data.get('status') == MarriageProposals.Status.COMPLETE):
                if instance.sender.gender == User.Gender.MAN:
                    Marriage.objects.create(
                        husband=instance.sender,
                        wife=instance.receiver,
                    )
                else:
                    Marriage.objects.create(
                        husband=instance.receiver,
                        wife=instance.sender,
                    )

                instance.sender.is_married = True
                instance.receiver.is_married = True
                instance.sender.save()
                instance.receiver.save()

                MarriageProposals.objects.filter(
                    models.Q(sender=instance.sender) |
                    models.Q(sender=instance.receiver) |
                    models.Q(receiver=instance.sender) |
                    models.Q(receiver=instance.receiver),
                    status=MarriageProposals.Status.WAITING
                ).exclude(id=instance.id).update(status=MarriageProposals.Status.CANCELED)

            serializer.save()

class OffersHTML(TemplateView):
    template_name = 'users/offers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Полученные
        incoming = MarriageProposals.objects.filter(
            receiver=self.request.user,
            status=MarriageProposals.Status.WAITING
        )
        # Отправленные заявки
        outgoing = MarriageProposals.objects.filter(
            sender=self.request.user,
            status=MarriageProposals.Status.WAITING
        )

        choice = MarriageProposals.Status

        context.update({
            'offers_incoming': incoming,
            'offers_outgoing': outgoing,
            'request': self.request,
            'choice': choice
        })

        return context


class DivorceAPI(
    mixins.UpdateModelMixin,
    generics.GenericAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DivorceSerializer

    def get_queryset(self):
        user = self.request.user
        return Marriage.objects.filter(
            (models.Q(husband=user) | models.Q(wife=user)),
            status=Marriage.Status.ACTIVE
        )

    def get_object(self):
        queryset = self.get_queryset()
        if not queryset.exists():
            raise NotFound("Вы не состоите в активном браке")
        return queryset.first()

    def perform_update(self, serializer):
        marriage = serializer.instance

        with transaction.atomic():
            husband = marriage.husband
            wife = marriage.wife
            husband.is_married = False
            wife.is_married = False
            husband.save()
            wife.save()

            marriage.status = Marriage.Status.DIVORCED
            marriage.save()

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            return Response({"detail": "Брак расторгнут успешно"}, status=status.HTTP_200_OK)
        return response

    def patch(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class MarriagesHTML(TemplateView):
    template_name = 'users/marriages-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        marriages = Marriage.objects.filter(
            models.Q(husband=self.request.user) | models.Q(wife=self.request.user)
        )

        marriages_data = []
        for marriage in marriages.select_related('husband', 'wife'):
            partner = marriage.wife if marriage.husband == self.request.user else marriage.husband
            marriages_data.append({
                'partner': partner,
                'start_date': marriage.created_at.strftime("%d.%m.%Y"),
                'end_date': marriage.updated_at.strftime(
                    "%d.%m.%Y") if marriage.status != Marriage.Status.ACTIVE else None,
                'is_active': marriage.status == Marriage.Status.ACTIVE,
                'partner_photo': getattr(partner, 'has_photo', '/media/users/default.png')
            })

        marriages_data.sort(key=lambda x: x['start_date'], reverse=True)

        active_marriage = next((m for m in marriages_data if m['is_active']), None)  # Первый активный (или None)
        past_marriages = [m for m in marriages_data if not m['is_active']]  # Список прошедших

        context.update({
            'active_marriage': active_marriage,
            'past_marriages': past_marriages,
            'request': self.request
        })
        return context
