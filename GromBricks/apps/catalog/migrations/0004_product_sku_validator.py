import apps.catalog.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0003_seed_zane_golden_weapons'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='sku',
            field=models.CharField(
                max_length=50,
                unique=True,
                validators=[apps.catalog.validators.validate_product_sku],
                verbose_name='артикул',
            ),
        ),
    ]
