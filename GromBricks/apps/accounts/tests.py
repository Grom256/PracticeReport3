from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AccountFlowTests(TestCase):
    def test_registration_creates_user_and_logs_them_in(self):
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

        self.assertRedirects(response, reverse('accounts:profile'))
        self.assertTrue(User.objects.filter(username='brickfan').exists())
        self.assertEqual(int(self.client.session['_auth_user_id']), User.objects.get(username='brickfan').pk)

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
