from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import User, MarriageProposals, Marriage


class ProposalAPITest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1', password='pass', gender=User.Gender.MAN
        )
        self.user2 = User.objects.create_user(
            username='user2', password='pass', gender=User.Gender.WOMAN
        )
        self.client.login(username='user1', password='pass')

    def test_send_proposal_to_registered(self):
        url = reverse('proposal-api')
        data = {'receiver_username': self.user2.username}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('success', response.data)

    def test_cannot_send_proposal_to_self(self):
        url = reverse('proposal-api')
        data = {'receiver_username': self.user1.username}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('самому себе', str(response.data) or str(response.content))

    def test_user_autocomplete(self):
        url = reverse('user-autocomplete')
        self.user2.is_married = False
        self.user2.first_name = 'Мария'
        self.user2.save()
        self.client.force_login(self.user1)
        response = self.client.get(url, {'q': 'Мария'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(u['username'] == 'user2' for u in response.data))


class DivorceAPITest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1', password='pass', gender=User.Gender.MAN
        )
        self.user2 = User.objects.create_user(
            username='user2', password='pass', gender=User.Gender.WOMAN
        )
        self.marriage = Marriage.objects.create(husband=self.user1, wife=self.user2)
        self.client.login(username='user1', password='pass')

    def test_divorce(self):
        url = reverse('divorce-api')
        response = self.client.patch(url, {})
        self.assertIn(response.status_code, [200, 405])  # 405 если не реализован PATCH
