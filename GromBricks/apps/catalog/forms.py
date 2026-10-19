from django import forms

from .models import Product


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
