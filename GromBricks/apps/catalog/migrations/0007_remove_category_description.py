
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0006_stocknotification_wishlistitem'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='description',
        ),
    ]
