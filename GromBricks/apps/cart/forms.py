from django import forms
from django.core.validators import MaxValueValidator

from .cart import MAX_CART_QUANTITY


class CartQuantityForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=MAX_CART_QUANTITY,
        widget=forms.NumberInput(attrs={'min': '1', 'max': str(MAX_CART_QUANTITY), 'step': '1', 'inputmode': 'numeric'}),
    )

    def __init__(self, *args, max_quantity=MAX_CART_QUANTITY, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['quantity']
        field.max_value = min(MAX_CART_QUANTITY, max(0, max_quantity))
        field.validators = [
            validator
            for validator in field.validators
            if not isinstance(validator, MaxValueValidator)
        ]
        field.validators.append(MaxValueValidator(field.max_value))
        field.widget.attrs['max'] = str(field.max_value)
