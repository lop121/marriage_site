from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import Marriage, MarriageProposals

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.man = User.objects.create_user(
            username='ivan', password='pass', first_name='Иван', last_name='Иванов', gender=User.Gender.MAN
        )
        self.woman = User.objects.create_user(
            username='maria', password='pass', first_name='Мария', last_name='Петрова', gender=User.Gender.WOMAN
        )

    def test_user_creation(self):
        self.assertEqual(self.man.first_name, 'Иван')
        self.assertEqual(self.woman.gender, User.Gender.WOMAN)
        self.assertFalse(self.man.is_married)

    def test_has_photo_default(self):
        self.assertIn('users/default.png', self.man.has_photo)

    def test_str(self):
        self.assertEqual(str(self.man), 'ivan')

class MarriageModelTest(TestCase):
    def setUp(self):
        self.man = User.objects.create_user(
            username='ivan', password='pass', first_name='Иван', last_name='Иванов', gender=User.Gender.MAN
        )
        self.woman = User.objects.create_user(
            username='maria', password='pass', first_name='Мария', last_name='Петрова', gender=User.Gender.WOMAN
        )
        self.marriage = Marriage.objects.create(husband=self.man, wife=self.woman)

    def test_marriage_creation(self):
        self.assertEqual(self.marriage.husband, self.man)
        self.assertEqual(self.marriage.wife, self.woman)
        self.assertEqual(self.marriage.status, Marriage.Status.ACTIVE)

    def test_str(self):
        self.assertEqual(str(self.marriage), 'ivan + maria')

    def test_display_partner(self):
        self.assertEqual(self.marriage.display_partner(self.man), self.woman.get_full_name())
        self.assertEqual(self.marriage.display_partner(self.woman), self.man.get_full_name())

    def test_active_marriage_and_partner_property(self):
        # Проверяем, что у пользователя появился активный брак и partner
        self.assertEqual(self.man.active_marriage, self.marriage)
        self.assertEqual(self.man.partner, self.woman)
        self.assertEqual(self.woman.partner, self.man)

class MarriageProposalsModelTest(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(
            username='sender', password='pass', first_name='Сергей', last_name='Сидоров', gender=User.Gender.MAN
        )
        self.receiver = User.objects.create_user(
            username='receiver', password='pass', first_name='Ольга', last_name='Кузнецова', gender=User.Gender.WOMAN
        )
        self.proposal = MarriageProposals.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            status=MarriageProposals.Status.WAITING
        )

    def test_proposal_creation(self):
        self.assertEqual(self.proposal.sender, self.sender)
        self.assertEqual(self.proposal.receiver, self.receiver)
        self.assertEqual(self.proposal.status, MarriageProposals.Status.WAITING)

    def test_str(self):
        self.assertEqual(str(self.proposal), 'sender -> receiver')

    def test_status_display(self):
        self.assertEqual(self.proposal.status_display, 'WAITING')

    def test_display_receiver(self):
        self.assertEqual(self.proposal.display_receiver, self.receiver.get_full_name())
        # Для незарегистрированного пользователя
        proposal2 = MarriageProposals.objects.create(
            sender=self.sender,
            receiver=None,
            receiver_fullname='Анна Иванова',
            status=MarriageProposals.Status.WAITING
        )
        self.assertEqual(proposal2.display_receiver, 'Анна Иванова')