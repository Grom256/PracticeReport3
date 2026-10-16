from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = (
            'recipient_name',
            'phone',
            'city',
            'address',
            'postal_code',
            'delivery_service',
            'payment_method',
        )
        labels = {
            'recipient_name': 'Ім’я та прізвище одержувача',
            'phone': 'Телефон одержувача',
            'city': 'Місто',
            'address': 'Відділення або адреса доставки',
            'postal_code': 'Поштовий індекс (необов’язково)',
            'delivery_service': 'Служба доставки',
            'payment_method': 'Спосіб оплати',
        }
        widgets = {
            'recipient_name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'phone': forms.TelInput(attrs={'autocomplete': 'tel', 'placeholder': '+380'}),
            'city': forms.TextInput(attrs={'autocomplete': 'address-level2'}),
            'address': forms.TextInput(attrs={'autocomplete': 'street-address'}),
            'postal_code': forms.TextInput(attrs={'autocomplete': 'postal-code'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            full_name = f'{user.first_name} {user.last_name}'.strip()
            if full_name:
                self.fields['recipient_name'].initial = full_name
