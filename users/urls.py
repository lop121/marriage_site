from django.contrib.auth.views import LogoutView
from django.urls import path, re_path

from . import views
from .views import UserAutocompleteView

urlpatterns = [
    path('', views.HomePage.as_view(), name='home'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.RegistrationUser.as_view(), name='register'),
    path('profile/', views.UserProfile.as_view(), name='profile'),
    path('proposal/', views.ProposalHTML.as_view(), name='proposal'),
    path('api/proposal/', views.ProposalAPI.as_view(), name='api-proposal'),
    path('offers/', views.OffersHTML.as_view(), name='offers-list'),
    path('api/offers/<int:pk>/', views.OffersAPI.as_view()),
    path('api/divorce/', views.DivorceAPI.as_view(), name='divorce'),
    path('marriages/', views.MarriagesHTML.as_view(), name='marriages-list'),
    path('api/users/autocomplete/', UserAutocompleteView.as_view(), name='user-autocomplete'),


]