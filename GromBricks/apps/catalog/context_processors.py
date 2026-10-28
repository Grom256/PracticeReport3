def wishlist_summary(request):
    """Provides user's wishlist count and active product IDs across all templates."""
    if not request.user.is_authenticated:
        return {'wishlist_count': 0, 'wishlist_product_ids': set()}

    items = request.user.wishlist_items.values_list('product_id', flat=True)
    product_ids = set(items)
    return {
        'wishlist_count': len(product_ids),
        'wishlist_product_ids': product_ids,
    }
