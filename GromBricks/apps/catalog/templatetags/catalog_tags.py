from django import template


register = template.Library()


@register.simple_tag
def stock_status(product):
    """Return a concise, reusable availability label for a product."""
    return 'В наявності' if product.stock_quantity > 0 else 'Немає в наявності'
