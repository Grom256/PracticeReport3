from .cart import positive_integer


def cart_summary(request):
    stored_items = request.session.get('cart', {})
    items = stored_items.values() if isinstance(stored_items, dict) else ()
    count = 0
    for item in items:
        quantity = positive_integer(item.get('quantity')) if isinstance(item, dict) else None
        if quantity:
            count += quantity
    return {'cart_count': count}
