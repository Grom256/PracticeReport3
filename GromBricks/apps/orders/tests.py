from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product

from .models import Order, OrderItem

User = get_user_model()


class OrderFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='Safe-demo-pass-842!')
        self.category = Category.objects.create(name='Космос', slug='kosmos')
        self.product = Product.objects.create(
            category=self.category,
            product_type=Product.ProductType.MINIFIGURE,
            sku='FIG-001',
            name='Космічна фігурка',
            condition=Product.Condition.NEW,
            price=Decimal('125.00'),
            stock_quantity=3,
        )
        self.client.force_login(self.user)
        self.client.post(
            reverse('cart:add', args=[self.product.pk]), {'quantity': 2}
        )
        self.checkout_data = {
            'recipient_name': 'Олена Тестова',
            'phone': '+380501112233',
            'city': 'Київ',
            'address': 'Відділення №1',
            'postal_code': '',
            'delivery_service': 'nova_poshta',
            # A client-supplied payment choice must not replace the server choice.
            'payment_method': 'bank_transfer',
        }

    def test_checkout_creates_order_snapshots_price_and_decrements_stock(self):
        response = self.client.post(reverse('orders:checkout'), self.checkout_data)

        order = Order.objects.get(user=self.user)
        self.assertEqual(order.payment_method, Order.PaymentMethod.CASH_ON_DELIVERY)
        self.assertRedirects(response, reverse('orders:detail', args=[order.pk]))
        item = OrderItem.objects.get(order=order, product=self.product)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, Decimal('125.00'))
        self.assertEqual(self.product.__class__.objects.get(pk=self.product.pk).stock_quantity, 1)
        self.assertIsNone(self.client.session.get('cart'))

        self.product.price = Decimal('200.00')
        self.product.save(update_fields=['price', 'updated_at'])
        self.assertEqual(OrderItem.objects.get(pk=item.pk).line_total, Decimal('250.00'))
        self.assertEqual(self.client.get(reverse('orders:detail', args=[order.pk])).status_code, 200)

    def test_checkout_rejects_inventory_that_changed(self):
        Product.objects.filter(pk=self.product.pk).update(stock_quantity=1)

        response = self.client.post(reverse('orders:checkout'), self.checkout_data)

        self.assertRedirects(response, reverse('cart:detail'))
        self.assertFalse(Order.objects.filter(user=self.user).exists())
        self.assertEqual(self.client.session['cart'][str(self.product.pk)]['quantity'], 2)

    def test_checkout_rejects_session_quantity_above_cart_limit(self):
        session = self.client.session
        session['cart'][str(self.product.pk)]['quantity'] = 1000
        session.save()

        response = self.client.post(reverse('orders:checkout'), self.checkout_data)

        self.assertRedirects(response, reverse('cart:detail'))
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def test_order_history_and_detail_are_private_to_owner(self):
        response = self.client.post(reverse('orders:checkout'), self.checkout_data)
        order = Order.objects.get(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(reverse('orders:list')).status_code, 200)

        other_user = User.objects.create_user(username='other', password='Safe-demo-pass-842!')
        self.client.force_login(other_user)
        self.assertEqual(
            self.client.get(reverse('orders:detail', args=[order.pk])).status_code,
            404,
        )


    def test_checkout_applies_tiered_discount(self):
        expensive_product = Product.objects.create(
            category=self.category,
            product_type=Product.ProductType.MINIFIGURE,
            sku='EXP-001',
            name='Колекційний набір',
            condition=Product.Condition.NEW,
            price=Decimal('3000.00'),
            stock_quantity=5,
        )
        self.client.post(reverse('cart:remove', args=[self.product.pk]))
        self.client.post(reverse('cart:add', args=[expensive_product.pk]), {'quantity': 2})
        # 2 * 3000 = 6000 UAH > 5000 -> 10% discount (600 UAH), total = 5400 UAH

        response = self.client.post(reverse('orders:checkout'), self.checkout_data)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.subtotal, Decimal('6000.00'))
        self.assertEqual(order.discount_percent, 10)
        self.assertEqual(order.discount_amount, Decimal('600.00'))
        self.assertEqual(order.total_amount, Decimal('5400.00'))
