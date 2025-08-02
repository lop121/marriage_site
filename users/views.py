from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, TemplateView, View, DetailView

from users.forms import LoginUserForm, RegisterUserForm, ProfileUserForm, MarriageProposalForm
from users.models import User, Marriage, MarriageProposals


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


class UserProfile(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user  # type: User

        context.update({
            'is_married': user.is_married,
            'partner_name': user.partner,
        })

        return context

    def get_success_url(self):
        return reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user


class UserPublicProfileView(DetailView):
    model = get_user_model()
    template_name = 'users/public_profile.html'
    context_object_name = 'profile_user'


class DeletePhotoView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        if user.photo:
            user.photo.delete(save=True)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Нет фото'}, status=400)


class ProposalHTML(LoginRequiredMixin, TemplateView):
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


class MarriagesHTML(TemplateView):
    template_name = 'users/marriages-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        marriages = Marriage.objects.filter(
            models.Q(husband=self.request.user) | models.Q(wife=self.request.user)
        ).select_related('husband', 'wife')

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
