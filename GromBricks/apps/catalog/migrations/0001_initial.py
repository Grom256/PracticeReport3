
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='назва')),
                ('slug', models.SlugField(max_length=110, unique=True, verbose_name='URL-ідентифікатор')),
                ('description', models.TextField(blank=True, verbose_name='опис')),
                ('is_active', models.BooleanField(default=True, verbose_name='активна')),
            ],
            options={
                'verbose_name': 'категорія',
                'verbose_name_plural': 'категорії',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_type', models.CharField(choices=[('minifigure', 'Мініфігурка'), ('part', 'Деталь')], max_length=12, verbose_name='тип товару')),
                ('sku', models.CharField(max_length=50, unique=True, verbose_name='артикул')),
                ('name', models.CharField(max_length=200, verbose_name='назва')),
                ('description', models.TextField(blank=True, verbose_name='опис')),
                ('series', models.CharField(blank=True, max_length=100, verbose_name='серія / тематика')),
                ('color', models.CharField(blank=True, max_length=60, verbose_name='колір')),
                ('condition', models.CharField(choices=[('new', 'Новий'), ('used', 'Вживаний')], default='new', max_length=10, verbose_name='стан')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='ціна')),
                ('stock_quantity', models.PositiveIntegerField(default=0, verbose_name='кількість на складі')),
                ('image', models.ImageField(blank=True, upload_to='products/%Y/%m/', verbose_name='зображення')),
                ('is_rare', models.BooleanField(default=False, verbose_name='рідкісний товар')),
                ('is_active', models.BooleanField(default=True, verbose_name='показувати в каталозі')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='створено')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='оновлено')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='catalog.category', verbose_name='категорія')),
            ],
            options={
                'verbose_name': 'товар',
                'verbose_name_plural': 'товари',
                'ordering': ['name'],
                'constraints': [models.CheckConstraint(condition=models.Q(('price__gte', 0)), name='product_price_nonnegative')],
            },
        ),
    ]
