from django.db import migrations, models


def migrate_payment_method_forward(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    Order.objects.exclude(payment_method='cash_on_delivery').update(
        payment_method='cash_on_delivery'
    )


def migrate_payment_method_backward(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    Order.objects.filter(payment_method='cash_on_delivery').update(
        payment_method='bank_transfer'
    )


class Migration(migrations.Migration):
    dependencies = [('orders', '0001_initial')]

    operations = [
        migrations.RunPython(
            migrate_payment_method_forward,
            migrate_payment_method_backward,
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('cash_on_delivery', 'Накладений платіж (оплата при отриманні)')
                ],
                default='cash_on_delivery',
                max_length=20,
                verbose_name='спосіб оплати',
            ),
        ),
    ]
