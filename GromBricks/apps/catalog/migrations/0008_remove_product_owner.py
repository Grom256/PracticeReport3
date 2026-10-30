
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_remove_category_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='owner',
        ),
    ]
