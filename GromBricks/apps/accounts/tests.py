from django.core import mail
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Profile

User = get_user_model()


class AccountFlowTests(TestCase):
    def test_registration_flow_with_email_code_verification(self):
        # 1. Подання форми реєстрації
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'brickfan',
                'first_name': 'Олена',
                'last_name': 'Тестова',
                'email': 'olena@example.com',
                'password1': 'Safe-demo-pass-842!',
                'password2': 'Safe-demo-pass-842!',
            },
        )
        self.assertRedirects(response, reverse('accounts:verify_email'))

        # Перевірка, що користувач створений, але неактивний до підтвердження
        user = User.objects.get(username='brickfan')
        self.assertFalse(user.is_active)
        self.assertFalse(user.profile.is_email_verified)
        self.assertTrue(len(user.profile.verification_code) == 6)

        # Перевірка відправлення листа через Django mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(user.profile.verification_code, mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['olena@example.com'])

        # 2. Спроба ввести невірний код
        verify_fail = self.client.post(
            reverse('accounts:verify_email'),
            {'code': '000000'},
        )
        self.assertEqual(verify_fail.status_code, 200)
        self.assertContains(verify_fail, 'Невірний код')
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        # 3. Введення правильного коду
        correct_code = user.profile.verification_code
        verify_success = self.client.post(
            reverse('accounts:verify_email'),
            {'code': correct_code},
        )
        self.assertRedirects(verify_success, reverse('accounts:profile'))

        # Користувач активований і залогінений
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.profile.is_email_verified)
        self.assertEqual(user.profile.verification_code, '')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_resend_verification_code(self):
        self.client.post(
            reverse('accounts:register'),
            {
                'username': 'brickfan2',
                'first_name': 'Іван',
                'last_name': 'Тестовий',
                'email': 'ivan@example.com',
                'password1': 'Safe-demo-pass-842!',
                'password2': 'Safe-demo-pass-842!',
            },
        )
        user = User.objects.get(username='brickfan2')
        first_code = user.profile.verification_code

        # Запит нового коду
        resend_response = self.client.post(reverse('accounts:resend_code'))
        self.assertRedirects(resend_response, reverse('accounts:verify_email'))

        user.refresh_from_db()
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(user.profile.verification_code, mail.outbox[1].body)

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(username='existing', email='same@example.com', password='Safe-demo-pass-842!')
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'another',
                'email': 'SAME@example.com',
                'password1': 'Safe-demo-pass-842!',
                'password2': 'Safe-demo-pass-842!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'вже зареєстрований')
        self.assertFalse(User.objects.filter(username='another').exists())

    def test_profile_requires_login_and_saves_profile_fields(self):
        user = User.objects.create_user(username='brickfan', email='old@example.com', password='Safe-demo-pass-842!')
        Profile.objects.get_or_create(user=user)
        response = self.client.get(reverse('accounts:profile'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:profile')}")

        self.client.force_login(user)
        response = self.client.post(
            reverse('accounts:profile'),
            {'first_name': 'Олена', 'last_name': 'Тестова', 'email': 'new@example.com'},
        )
        self.assertRedirects(response, reverse('accounts:profile'))
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Олена')
        self.assertEqual(user.email, 'new@example.com')
