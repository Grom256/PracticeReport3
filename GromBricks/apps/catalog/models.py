from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from .validators import validate_product_sku


class Category(models.Model):
    name = models.CharField('назва', max_length=100, unique=True)
    slug = models.SlugField('URL-ідентифікатор', max_length=110, unique=True)
    is_active = models.BooleanField('активна', default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'категорія'
        verbose_name_plural = 'категорії'

    def __str__(self):
        return self.name


class Product(models.Model):
    class ProductType(models.TextChoices):
        MINIFIGURE = 'minifigure', 'Мініфігурка'
        PART = 'part', 'Деталь'

    class Condition(models.TextChoices):
        NEW = 'new', 'Новий'
        USED = 'used', 'Вживаний'

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='категорія',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='власник запису',
    )
    product_type = models.CharField(
        'тип товару', max_length=12, choices=ProductType.choices
    )
    sku = models.CharField(
        'артикул', max_length=50, unique=True, validators=[validate_product_sku]
    )
    name = models.CharField('назва', max_length=200)
    description = models.TextField('опис', blank=True)
    series = models.CharField('серія / тематика', max_length=100, blank=True)
    color = models.CharField('колір', max_length=60, blank=True)
    condition = models.CharField(
        'стан', max_length=10, choices=Condition.choices, default=Condition.NEW
    )
    price = models.DecimalField(
        'ціна', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    stock_quantity = models.PositiveIntegerField('кількість на складі', default=0)
    image = models.ImageField('зображення', upload_to='products/%Y/%m/', blank=True)
    is_rare = models.BooleanField('рідкісний товар', default=False)
    is_active = models.BooleanField('показувати в каталозі', default=True)
    created_at = models.DateTimeField('створено', auto_now_add=True)
    updated_at = models.DateTimeField('оновлено', auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'товар'
        verbose_name_plural = 'товари'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['product_type']),
            models.Index(fields=['-created_at']),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gte=0), name='product_price_nonnegative'),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._previous_stock = self.stock_quantity

    def __str__(self):
        return f'{self.name} ({self.sku})'

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_stock = getattr(self, '_previous_stock', 0)
        super().save(*args, **kwargs)
        new_stock = self.stock_quantity
        self._previous_stock = new_stock

        if (old_stock == 0 and new_stock > 0) or (is_new and new_stock > 0):
            try:
                from .services import process_stock_notifications
                process_stock_notifications(self)
            except Exception:
                pass


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        verbose_name='користувач',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        verbose_name='товар',
    )
    created_at = models.DateTimeField('додано', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'товар у списку бажань'
        verbose_name_plural = 'список бажань'
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_wishlist_user_product')
        ]

    def __str__(self):
        return f'{self.user.username} -> {self.product.name}'


class StockNotification(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        TELEGRAM = 'telegram', 'Telegram'
        BOTH = 'both', 'Email та Telegram'

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_notifications',
        verbose_name='товар',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_notifications',
        verbose_name='користувач',
    )
    channel = models.CharField(
        'канал сповіщення',
        max_length=10,
        choices=Channel.choices,
        default=Channel.EMAIL,
    )
    email = models.EmailField('email для сповіщення', blank=True)
    telegram_chat_id = models.CharField('Telegram Chat ID', max_length=50, blank=True)
    is_notified = models.BooleanField('сповіщення надіслано', default=False)
    notified_at = models.DateTimeField('час сповіщення', null=True, blank=True)
    created_at = models.DateTimeField('створено', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'підписка на сповіщення'
        verbose_name_plural = 'підписки на сповіщення'

    def __str__(self):
        return f'Сповіщення: {self.product.name} ({self.get_channel_display()})'
