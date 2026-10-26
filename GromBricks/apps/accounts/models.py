from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='користувач',
    )
    phone = models.CharField('телефон', max_length=30, blank=True)
    avatar = models.ImageField('аватар', upload_to='avatars/', blank=True)
    date_of_birth = models.DateField('дата народження', null=True, blank=True)
    is_email_verified = models.BooleanField('пошта підтверджена', default=False)
    verification_code = models.CharField('код підтвердження', max_length=6, blank=True)
    telegram_chat_id = models.CharField('Telegram Chat ID', max_length=50, blank=True)

    class Meta:
        verbose_name = 'профіль'
        verbose_name_plural = 'профілі'

    def __str__(self):
        return f'Профіль користувача {self.user.username}'
