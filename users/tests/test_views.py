from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class PublicViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='pass', gender=User.Gender.MAN,
            first_name='Иван', last_name='Иванов'
        )

    def test_homepage(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Главная страница')

    def test_login_page(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Авторизация')

    def test_registration_page(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Регистрация')

    def test_public_profile(self):
        response = self.client.get(reverse('public_profile', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.first_name)


class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='pass', gender=User.Gender.MAN,
            first_name='Иван', last_name='Иванов'
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # редирект на логин

    def test_profile_page(self):
        self.client.login(username='testuser', password='pass')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Профиль')
        self.assertContains(response, self.user.first_name)
