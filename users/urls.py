from django.contrib.auth.views import LogoutView
from django.urls import path, re_path

from . import views
from .views import ProposalAPI

urlpatterns = [
    path('', views.HomePage.as_view(), name='home'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.RegistrationUser.as_view(), name='register'),
    path('profile/', views.UserProfile.as_view(), name='profile'),
    path('api/proposal/', ProposalAPI.as_view(), name='proposal'),


]