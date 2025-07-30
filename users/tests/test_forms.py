from django.test import TestCase
from django.contrib.auth import get_user_model
from users.forms import RegisterUserForm, ProfileUserForm, MarriageProposalForm, LoginUserForm

User = get_user_model()

class RegisterUserFormTest(TestCase):
    def test_valid_registration(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password1': 'Testpass123',
            'password2': 'Testpass123',
            'gender': User.Gender.MAN,
        }
        form = RegisterUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password1': 'Testpass123',
            'password2': 'Wrongpass',
            'gender': User.Gender.MAN,
        }
        form = RegisterUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_duplicate_email(self):
        User.objects.create_user(username='existing', email='test@example.com', password='pass', gender=User.Gender.MAN)
        form_data = {
            'username': 'testuser2',
            'email': 'test@example.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password1': 'Testpass123',
            'password2': 'Testpass123',
            'gender': User.Gender.MAN,
        }
        form = RegisterUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

class ProfileUserFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='pass', gender=User.Gender.MAN,
            first_name='Иван', last_name='Иванов'
        )

    def test_profile_form_initial(self):
        form = ProfileUserForm(instance=self.user)
        self.assertEqual(form.initial['username'], 'testuser')
        self.assertEqual(form.initial['email'], 'test@example.com')

class MarriageProposalFormTest(TestCase):
    def test_valid_proposal(self):
        form_data = {
            'first_name': 'Анна',
            'last_name': 'Смирнова',
            'gender': User.Gender.WOMAN,
        }
        form = MarriageProposalForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_empty_form(self):
        form = MarriageProposalForm(data={})
        self.assertTrue(form.is_valid())  # Все поля не обязательные

class LoginUserFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='pass', gender=User.Gender.MAN
        )

    def test_login_valid(self):
        form = LoginUserForm(data={'username': 'testuser', 'password': 'pass'})
        self.assertTrue(form.is_valid())

    def test_login_invalid(self):
        form = LoginUserForm(data={'username': 'testuser', 'password': 'wrongpass'})
        self.assertFalse(form.is_valid())