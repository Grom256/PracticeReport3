from decimal import Decimal

from django.db import migrations


def add_zane_golden_weapons(apps, schema_editor):
    Category = apps.get_model('catalog', 'Category')
    Product = apps.get_model('catalog', 'Product')
    database = schema_editor.connection.alias

    category, _created = Category.objects.using(database).get_or_create(
        slug='ninjago',
        defaults={
            'name': 'Ninjago',
            'description': 'Мініфігурки та деталі серії LEGO Ninjago.',
            'is_active': True,
        },
    )
    Product.objects.using(database).get_or_create(
        sku='njo0001',
        defaults={
            'category_id': category.pk,
            'product_type': 'minifigure',
            'name': 'Zane Golden Weapons',
            'description': 'Мініфігурка Зейна з колекції Golden Weapons. Хороший стан.',
            'series': 'Ninjago',
            'condition': 'used',
            'price': Decimal('1199.00'),
            'stock_quantity': 1,
            'is_rare': False,
            'is_active': True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0002_product_owner'),
    ]

    operations = [
        # Keep seeded records when rolling back, so existing catalog data is never deleted.
        migrations.RunPython(add_zane_golden_weapons, migrations.RunPython.noop),
    ]
