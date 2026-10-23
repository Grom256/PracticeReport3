from django import forms

from .models import Order


class OrderCheckoutForm(forms.ModelForm):
    """Delivery and payment details supplied by the signed-in customer."""

    class Meta:
        model = Order
        fields = (
            'recipient_name',
            'phone',
            'city',
            'address',
            'postal_code',
            'delivery_service',
        )
        widgets = {
            'recipient_name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'phone': forms.TextInput(attrs={'autocomplete': 'tel'}),
            'city': forms.TextInput(attrs={'autocomplete': 'address-level2'}),
            'address': forms.TextInput(attrs={'autocomplete': 'street-address'}),
            'postal_code': forms.TextInput(attrs={'autocomplete': 'postal-code'}),
        }
