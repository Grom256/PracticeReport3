from decimal import Decimal

from apps.catalog.models import Product


class Cart:
    """Session-backed cart; prices are read from the current product records."""

    session_key = 'cart'

    def __init__(self, request):
        self.session = request.session
        self.items = self.session.get(self.session_key, {})

    def __iter__(self):
        product_ids = []
        for product_id in self.items:
            try:
                product_ids.append(int(product_id))
            except (TypeError, ValueError):
                continue

        products = Product.objects.filter(pk__in=product_ids).select_related('category')
        products_by_id = {str(product.pk): product for product in products}

        for product_id, stored in self.items.items():
            product = products_by_id.get(str(product_id))
            try:
                quantity = int(stored.get('quantity', 0))
            except (AttributeError, TypeError, ValueError):
                continue
            if product is None or quantity < 1:
                continue
            yield {
                'product': product,
                'quantity': quantity,
                'line_total': product.price * quantity,
            }

    def __len__(self):
        total = 0
        for item in self.items.values():
            try:
                total += max(0, int(item.get('quantity', 0)))
            except (AttributeError, TypeError, ValueError):
                continue
        return total

    @property
    def total(self):
        return sum((item['line_total'] for item in self), Decimal('0.00'))

    def quantity_for(self, product_id):
        try:
            return int(self.items.get(str(product_id), {}).get('quantity', 0))
        except (AttributeError, TypeError, ValueError):
            return 0

    def add(self, product, quantity):
        product_id = str(product.pk)
        self.items[product_id] = {'quantity': self.quantity_for(product.pk) + quantity}
        self._save()

    def update(self, product_id, quantity):
        self.items[str(product_id)] = {'quantity': quantity}
        self._save()

    def remove(self, product_id):
        self.items.pop(str(product_id), None)
        self._save()

    def _save(self):
        self.session[self.session_key] = self.items
        self.session.modified = True
