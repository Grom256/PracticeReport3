from django import forms

from .models import Product, StockNotification


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'category',
            'product_type',
            'sku',
            'name',
            'description',
            'series',
            'color',
            'condition',
            'price',
            'stock_quantity',
            'image',
            'is_rare',
            'is_active',
        )
        widgets = {
            'category': forms.Select(),
            'product_type': forms.Select(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'condition': forms.Select(),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock_quantity': forms.NumberInput(attrs={'min': '0'}),
        }


class StockNotificationForm(forms.ModelForm):
    class Meta:
        model = StockNotification
        fields = ('channel', 'email', 'telegram_chat_id')
        labels = {
            'channel': 'Куди надіслати сповіщення',
            'email': 'Ваш Email',
            'telegram_chat_id': 'Ваш Telegram Chat ID',
        }
        widgets = {
            'channel': forms.RadioSelect(),
            'email': forms.EmailInput(attrs={'placeholder': 'name@example.com', 'class': 'form-input'}),
            'telegram_chat_id': forms.TextInput(attrs={'placeholder': 'Наприклад: 123456789', 'class': 'form-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        channel = cleaned_data.get('channel')
        email = (cleaned_data.get('email') or '').strip()
        telegram_chat_id = (cleaned_data.get('telegram_chat_id') or '').strip()

        if channel in (StockNotification.Channel.EMAIL, StockNotification.Channel.BOTH) and not email:
            self.add_error('email', 'Вкажіть email для отримання сповіщення.')
        if channel in (StockNotification.Channel.TELEGRAM, StockNotification.Channel.BOTH) and not telegram_chat_id:
            self.add_error('telegram_chat_id', 'Вкажіть Telegram Chat ID або підключіть бота.')

        return cleaned_data
