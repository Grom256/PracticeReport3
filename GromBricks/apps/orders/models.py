from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import ExpressionWrapper, F, Sum

from apps.catalog.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Нове'
        PROCESSING = 'processing', 'В обробці'
        SHIPPED = 'shipped', 'Відправлено'
        DELIVERED = 'delivered', 'Доставлено'
        CANCELLED = 'cancelled', 'Скасовано'

    class PaymentMethod(models.TextChoices):
        CASH_ON_DELIVERY = 'cash_on_delivery', 'Оплата при отриманні'
        BANK_TRANSFER = 'bank_transfer', 'Банківський переказ вручну'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name='користувач',
    )
    recipient_name = models.CharField('отримувач', max_length=150)
    phone = models.CharField('телефон', max_length=30)
    city = models.CharField('місто', max_length=100)
    address = models.CharField('адреса доставки', max_length=255)
    postal_code = models.CharField('поштовий індекс', max_length=20, blank=True)
    payment_method = models.CharField(
        'спосіб оплати', max_length=20, choices=PaymentMethod.choices
    )
    status = models.CharField(
        'статус', max_length=12, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField('створено', auto_now_add=True)
    updated_at = models.DateTimeField('оновлено', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'замовлення'
        verbose_name_plural = 'замовлення'

    def __str__(self):
        return f'Замовлення №{self.pk}'

    @property
    def total_amount(self):
        total = self.items.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('quantity') * F('unit_price'),
                    output_field=models.DecimalField(max_digits=20, decimal_places=2),
                )
            )
        )['total']
        return total if total is not None else Decimal('0.00')


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items', verbose_name='замовлення'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='товар',
    )
    quantity = models.PositiveIntegerField('кількість')
    unit_price = models.DecimalField('ціна на момент покупки', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'позиція замовлення'
        verbose_name_plural = 'позиції замовлення'
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name='order_item_quantity_positive'),
            models.CheckConstraint(condition=models.Q(unit_price__gte=0), name='order_item_price_nonnegative'),
            models.UniqueConstraint(fields=['order', 'product'], name='unique_product_per_order'),
        ]

    def __str__(self):
        return f'{self.product} × {self.quantity}'
