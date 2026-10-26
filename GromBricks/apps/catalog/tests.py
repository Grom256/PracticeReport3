import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.accounts.models import Profile

from .models import Category, Product, StockNotification, WishlistItem

User = get_user_model()


class CatalogTemplateTagTests(SimpleTestCase):
    def test_stock_status_tag_renders_availability(self):
        template = Template('{% load catalog_tags %}{% stock_status product %}')

        self.assertEqual(
            template.render(Context({'product': type('ProductStub', (), {'stock_quantity': 3})()})),
            'В наявності',
        )
        self.assertEqual(
            template.render(Context({'product': type('ProductStub', (), {'stock_quantity': 0})()})),
            'Немає в наявності',
        )


class TelegramSyncTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='telegram-user', password='password123')
        Profile.objects.create(user=self.user)
        self.client.force_login(self.user)

    def test_sync_requires_post(self):
        response = self.client.get(reverse('catalog:telegram_sync'))
        self.assertEqual(response.status_code, 405)

    @patch('apps.catalog.services.send_telegram_message')
    @patch('apps.catalog.services.urllib.request.urlopen')
    def test_sync_uses_only_exact_user_deep_link(self, mock_urlopen, mock_send_message):
        response = mock_urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps(
            {
                'ok': True,
                'result': [
                    {'message': {'text': f'/start user_{self.user.pk}', 'chat': {'id': 1001}}},
                    {'message': {'text': '/start', 'chat': {'id': 2002}}},
                ],
            }
        ).encode('utf-8')

        self.client.post(reverse('catalog:telegram_sync'))

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.telegram_chat_id, '1001')
        mock_send_message.assert_called_once()


class CatalogManagementAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Фігурки спец', slug='figures-spec')
        cls.staff = User.objects.create_user(
            username='staff', password='pass12345', is_staff=True
        )
        cls.product = Product.objects.create(
            name='Тестова фігурка',
            product_type=Product.ProductType.MINIFIGURE,
            sku='TEST-1',
            category=cls.category,
            condition=Product.Condition.NEW,
            price='100.00',
            stock_quantity=1,
            owner=cls.staff,
        )
        cls.customer = User.objects.create_user(username='customer', password='pass12345')
        cls.other_staff = User.objects.create_user(
            username='other-staff', password='pass12345', is_staff=True
        )

    @classmethod
    def management_urls(cls):
        return (
            reverse('catalog:product_manage_list'),
            reverse('catalog:product_create'),
            reverse('catalog:product_update', args=[cls.product.pk]),
            reverse('catalog:product_delete', args=[cls.product.pk]),
        )

    def test_guest_is_redirected_from_every_management_url(self):
        for url in self.management_urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('accounts:login'), response.url)

    def test_regular_user_is_forbidden_from_every_management_url(self):
        self.client.force_login(self.customer)
        for url in self.management_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_staff_can_open_every_management_url(self):
        self.client.force_login(self.staff)
        for url in self.management_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_staff_cannot_edit_or_delete_another_staff_members_product(self):
        self.client.force_login(self.other_staff)
        for url in (
            reverse('catalog:product_update', args=[self.product.pk]),
            reverse('catalog:product_delete', args=[self.product.pk]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_product_creator_is_saved_as_owner(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('catalog:product_create'),
            {
                'category': self.category.pk,
                'product_type': Product.ProductType.PART,
                'sku': 'NEW-PART-1',
                'name': 'Нова деталь',
                'condition': Product.Condition.NEW,
                'price': '25.00',
                'stock_quantity': 3,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.get(sku='NEW-PART-1').owner, self.staff)


class WishlistTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='collector', password='password123')
        self.category, _ = Category.objects.get_or_create(name='Ninjago-Test', defaults={'slug': 'ninjago-test'})
        self.product_in_stock = Product.objects.create(
            name='Lloyd Golden',
            category=self.category,
            product_type=Product.ProductType.MINIFIGURE,
            sku='NJO-101',
            price=Decimal('500.00'),
            stock_quantity=5,
        )
        self.product_out_of_stock = Product.objects.create(
            name='Sensei Wu Rare',
            category=self.category,
            product_type=Product.ProductType.MINIFIGURE,
            sku='NJO-102',
            price=Decimal('1500.00'),
            stock_quantity=0,
        )
        self.client.force_login(self.user)

    def test_wishlist_toggle_adds_and_removes_both_instock_and_out_of_stock(self):
        # Toggle in-stock product
        res1 = self.client.post(reverse('catalog:wishlist_toggle', args=[self.product_in_stock.pk]))
        self.assertTrue(WishlistItem.objects.filter(user=self.user, product=self.product_in_stock).exists())

        # Toggle out-of-stock product
        res2 = self.client.post(reverse('catalog:wishlist_toggle', args=[self.product_out_of_stock.pk]))
        self.assertTrue(WishlistItem.objects.filter(user=self.user, product=self.product_out_of_stock).exists())

        # Both exist in wishlist view
        wishlist_res = self.client.get(reverse('catalog:wishlist'))
        self.assertEqual(wishlist_res.status_code, 200)
        self.assertContains(wishlist_res, 'Lloyd Golden')
        self.assertContains(wishlist_res, 'Sensei Wu Rare')

        # Toggle in-stock product again -> removes it
        res3 = self.client.post(reverse('catalog:wishlist_toggle', args=[self.product_in_stock.pk]))
        self.assertFalse(WishlistItem.objects.filter(user=self.user, product=self.product_in_stock).exists())
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 1)


class StockNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ninja', email='ninja@example.com', password='password123')
        Profile.objects.create(user=self.user, telegram_chat_id='123456789')
        self.category, _ = Category.objects.get_or_create(name='Star Wars Test', defaults={'slug': 'star-wars-test'})
        self.product = Product.objects.create(
            name='Darth Vader Chrome',
            category=self.category,
            product_type=Product.ProductType.MINIFIGURE,
            sku='SW-001',
            price=Decimal('2800.00'),
            stock_quantity=0,
        )
        self.client.force_login(self.user)

    @patch('apps.catalog.services.send_telegram_message')
    @patch('apps.catalog.services.send_mail')
    def test_subscribe_and_automatic_stock_notification(self, mock_email, mock_tg):
        mock_tg.return_value = True
        mock_email.return_value = 1

        # Subscribe via both channels
        response = self.client.post(
            reverse('catalog:stock_notify', args=[self.product.pk]),
            {
                'channel': StockNotification.Channel.BOTH,
                'email': 'ninja@example.com',
                'telegram_chat_id': '123456789',
            }
        )
        self.assertEqual(response.status_code, 302)

        sub = StockNotification.objects.get(product=self.product, user=self.user)
        self.assertEqual(sub.channel, StockNotification.Channel.BOTH)
        self.assertFalse(sub.is_notified)

        # Restock product (stock 0 -> 2)
        self.product.stock_quantity = 2
        self.product.save()

        sub.refresh_from_db()
        self.assertTrue(sub.is_notified)
        self.assertIsNotNone(sub.notified_at)
        self.assertTrue(mock_email.called)
        self.assertTrue(mock_tg.called)
