def cart_summary(request):
    items = request.session.get('cart', {}).values()
    count = 0
    for item in items:
        try:
            count += max(0, int(item.get('quantity', 0)))
        except (AttributeError, TypeError, ValueError):
            continue
    return {'cart_count': count}
