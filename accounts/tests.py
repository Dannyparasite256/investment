from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.otp import PURPOSE_LOGIN, send_email_otp, verify_email_otp

User = get_user_model()


class AuthFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='user@test.com', password='TestPass123!')
        cache.clear()

    def test_register_page(self):
        r = self.client.get(reverse('accounts:register'))
        self.assertEqual(r.status_code, 200)

    def test_login_success(self):
        # Disable email OTP for this legacy path test
        self.user.email_otp_login = False
        self.user.save(update_fields=['email_otp_login'])
        r = self.client.post(reverse('accounts:login'), {
            'username': 'user@test.com',
            'password': 'TestPass123!',
        })
        self.assertEqual(r.status_code, 302)

    def test_dashboard_requires_login(self):
        r = self.client.get(reverse('core:dashboard'))
        self.assertEqual(r.status_code, 302)


@override_settings(
    EMAIL_OTP_LOGIN_REQUIRED=True,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_OTP_RESEND_SECONDS=0,
)
class EmailOTPLoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='otp@test.com',
            password='TestPass123!',
            email_otp_login=True,
            two_factor_enabled=False,
        )
        cache.clear()
        mail.outbox.clear()

    def test_login_requires_email_otp(self):
        r = self.client.post(reverse('accounts:login'), {
            'username': 'otp@test.com',
            'password': 'TestPass123!',
        })
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/2fa/email/', r['Location'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Login verification', mail.outbox[0].subject)

    def test_email_otp_verify_completes_login(self):
        send = send_email_otp(self.user, PURPOSE_LOGIN, force=True)
        self.assertTrue(send.ok)
        # Extract code from email body
        body = mail.outbox[-1].body
        code = None
        for part in body.split():
            if part.isdigit() and len(part) == 6:
                code = part
                break
        self.assertIsNotNone(code)

        session = self.client.session
        session['pre_2fa_user_id'] = self.user.pk
        session['pre_2fa_remember'] = True
        session['pre_2fa_method'] = 'email'
        session.save()

        r = self.client.post(reverse('accounts:verify_email_otp'), {'code': code})
        self.assertEqual(r.status_code, 302)
        # Authenticated
        r2 = self.client.get(reverse('core:dashboard'))
        self.assertEqual(r2.status_code, 200)

    def test_wrong_code_rejected(self):
        send_email_otp(self.user, PURPOSE_LOGIN, force=True)
        bad = verify_email_otp(self.user, PURPOSE_LOGIN, '000000')
        self.assertFalse(bad.ok)

    def test_api_login_otp_flow(self):
        from rest_framework.test import APIClient

        api = APIClient()
        r = api.post('/api/v1/auth/token/', {'username': 'otp@test.com', 'password': 'TestPass123!'}, format='json')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get('requires_otp'))
        self.assertEqual(data.get('method'), 'email')
        self.assertNotIn('token', data)

        body = mail.outbox[-1].body
        code = next(p for p in body.split() if p.isdigit() and len(p) == 6)
        r2 = api.post(
            '/api/v1/auth/token/',
            {
                'username': 'otp@test.com',
                'password': 'TestPass123!',
                'otp_code': code,
                'otp_method': 'email',
            },
            format='json',
        )
        self.assertEqual(r2.status_code, 200)
        self.assertIn('token', r2.json())
