from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from .validators import validate_product_sku


class Category(models.Model):
    name = models.CharField('назва', max_length=100, unique=True)
    slug = models.SlugField('URL-ідентифікатор', max_length=110, unique=True)
    description = models.TextField('опис', blank=True)
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
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gte=0), name='product_price_nonnegative'),
        ]

    def __str__(self):
        return f'{self.name} ({self.sku})'

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'pk': self.pk})
