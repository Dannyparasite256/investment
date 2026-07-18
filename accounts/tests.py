from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AuthFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='user@test.com', password='TestPass123!')

    def test_register_page(self):
        r = self.client.get(reverse('accounts:register'))
        self.assertEqual(r.status_code, 200)

    def test_login_success(self):
        r = self.client.post(reverse('accounts:login'), {
            'username': 'user@test.com',
            'password': 'TestPass123!',
        })
        self.assertEqual(r.status_code, 302)

    def test_dashboard_requires_login(self):
        r = self.client.get(reverse('core:dashboard'))
        self.assertEqual(r.status_code, 302)
