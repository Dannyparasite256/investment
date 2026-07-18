from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class StaffPanelAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='u@test.com', password='UserPass123!')
        self.staff = User.objects.create_user(
            email='s@test.com', password='StaffPass123!', is_staff=True,
        )

    def test_user_denied(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse('staffpanel:dashboard'))
        self.assertEqual(r.status_code, 403)

    def test_staff_ok(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('staffpanel:dashboard'))
        self.assertEqual(r.status_code, 200)
