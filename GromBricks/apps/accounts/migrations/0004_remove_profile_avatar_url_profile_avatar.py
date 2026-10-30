
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_profile_telegram_chat_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='avatar_url',
        ),
        migrations.AddField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, upload_to='avatars/', verbose_name='аватар'),
        ),
    ]
