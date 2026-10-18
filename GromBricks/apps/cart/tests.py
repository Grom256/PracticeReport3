from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product

User = get_user_model()


class SessionCartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='Safe-demo-pass-842!')
        self.category = Category.objects.create(name='Космос', slug='kosmos')
        self.product = Product.objects.create(
            category=self.category,
            product_type=Product.ProductType.PART,
            sku='PART-001',
            name='Золота деталь',
            condition=Product.Condition.NEW,
            price=Decimal('25.50'),
            stock_quantity=2,
        )
        self.client.force_login(self.user)

    def test_add_and_remove_product(self):
        response = self.client.post(
            reverse('cart:add', args=[self.product.pk]), {'quantity': 2}
        )
        self.assertRedirects(
            response,
            reverse('catalog:product_detail', args=[self.product.pk]),
        )
        self.assertEqual(self.client.session['cart'][str(self.product.pk)]['quantity'], 2)

        response = self.client.get(reverse('cart:detail'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '51,00 ₴')

        self.client.post(reverse('cart:remove', args=[self.product.pk]))
        self.assertNotIn(str(self.product.pk), self.client.session.get('cart', {}))

    def test_cart_rejects_quantity_above_inventory(self):
        self.client.post(reverse('cart:add', args=[self.product.pk]), {'quantity': 2})
        response = self.client.post(
            reverse('cart:add', args=[self.product.pk]), {'quantity': 1}
        )
        self.assertRedirects(
            response,
            reverse('catalog:product_detail', args=[self.product.pk]),
        )
        self.assertEqual(self.client.session['cart'][str(self.product.pk)]['quantity'], 2)

        self.client.post(
            reverse('cart:update', args=[self.product.pk]), {'quantity': 3}
        )
        self.assertEqual(self.client.session['cart'][str(self.product.pk)]['quantity'], 2)

    def test_guest_cannot_add_to_cart(self):
        self.client.logout()
        response = self.client.post(
            reverse('cart:add', args=[self.product.pk]), {'quantity': 1}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)
        self.assertEqual(self.client.session.get('cart', {}), {})
