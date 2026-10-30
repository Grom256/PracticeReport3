from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import connection
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.test.utils import CaptureQueriesContext

from .cart import Cart
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
        self.client.post(
            reverse('cart:update', args=[self.product.pk]), {'quantity': 3}
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

    def test_add_rejects_malformed_or_out_of_range_quantities(self):
        for quantity in ('abc', '-1', '0', '1.5', '1000', '9' * 5000):
            with self.subTest(quantity=str(quantity)[:20]):
                self.client.post(
                    reverse('cart:add', args=[self.product.pk]), {'quantity': quantity}
                )
                self.assertEqual(self.client.session.get('cart', {}), {})

    def test_update_rejects_malformed_quantities_without_changing_cart(self):
        self.client.post(reverse('cart:add', args=[self.product.pk]), {'quantity': 1})
        for quantity in ('abc', '-1', '0', '1.5', '1000'):
            with self.subTest(quantity=quantity):
                self.client.post(
                    reverse('cart:update', args=[self.product.pk]), {'quantity': quantity}
                )
                self.assertEqual(self.client.session['cart'][str(self.product.pk)]['quantity'], 1)

    def test_cart_loads_all_products_in_one_query(self):
        second_product = Product.objects.create(
            category=self.category,
            product_type=Product.ProductType.PART,
            sku='PART-002',
            name='Срібна деталь',
            condition=Product.Condition.NEW,
            price=Decimal('10.00'),
            stock_quantity=2,
        )
        request = RequestFactory().get('/cart/')
        SessionMiddleware(lambda _request: None).process_request(request)
        request.session['cart'] = {
            str(self.product.pk): {'quantity': 1},
            str(second_product.pk): {'quantity': 1},
        }

        with CaptureQueriesContext(connection) as queries:
            items = list(Cart(request))

        self.assertEqual(len(items), 2)
        self.assertEqual(len(queries), 1)

    def test_guest_cannot_add_to_cart(self):
        self.client.logout()
        response = self.client.post(
            reverse('cart:add', args=[self.product.pk]), {'quantity': 1}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)
        self.assertEqual(self.client.session.get('cart', {}), {})


class AutomaticDiscountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='shopper', password='password123')
        self.category = Category.objects.create(name='Castle', slug='castle')
        self.product1 = Product.objects.create(
            category=self.category,
            product_type=Product.ProductType.MINIFIGURE,
            sku='CAS-001',
            name='Лицар',
            price=Decimal('1000.00'),
            stock_quantity=10,
        )
        self.client.force_login(self.user)

    def test_no_discount_under_or_equal_2500(self):
        self.client.post(reverse('cart:add', args=[self.product1.pk]), {'quantity': 2})
        cart = Cart(self.client)
        self.assertEqual(cart.subtotal, Decimal('2000.00'))
        self.assertEqual(cart.discount_percent, 0)
        self.assertEqual(cart.discount_amount, Decimal('0.00'))
        self.assertEqual(cart.total, Decimal('2000.00'))

    def test_five_percent_discount_over_2500(self):
        self.client.post(reverse('cart:add', args=[self.product1.pk]), {'quantity': 3})
        cart = Cart(self.client)
        self.assertEqual(cart.subtotal, Decimal('3000.00'))
        self.assertEqual(cart.discount_percent, 5)
        self.assertEqual(cart.discount_amount, Decimal('150.00'))
        self.assertEqual(cart.total, Decimal('2850.00'))

    def test_ten_percent_discount_over_5000(self):
        self.client.post(reverse('cart:add', args=[self.product1.pk]), {'quantity': 6})
        cart = Cart(self.client)
        self.assertEqual(cart.subtotal, Decimal('6000.00'))
        self.assertEqual(cart.discount_percent, 10)
        self.assertEqual(cart.discount_amount, Decimal('600.00'))
        self.assertEqual(cart.total, Decimal('5400.00'))
