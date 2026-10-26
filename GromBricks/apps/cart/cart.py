from decimal import Decimal

from apps.catalog.models import Product

MAX_CART_QUANTITY = 999
DISCOUNT_THRESHOLD_TIER1 = Decimal('2500.00')
DISCOUNT_PERCENT_TIER1 = 5
DISCOUNT_THRESHOLD_TIER2 = Decimal('5000.00')
DISCOUNT_PERCENT_TIER2 = 10


def positive_integer(value):
    """Parse a positive integer from trusted or session data without coercion surprises."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and value.isascii() and value.isdigit() and len(value) <= 20:
        try:
            parsed = int(value)
        except ValueError:
            return None
        return parsed if parsed > 0 else None
    return None


class Cart:
    """Session-backed cart; prices are read from the current product records."""

    session_key = 'cart'

    def __init__(self, request):
        self.session = request.session
        stored_items = self.session.get(self.session_key, {})
        self.items = {}
        if isinstance(stored_items, dict):
            for raw_product_id, item in stored_items.items():
                product_id = positive_integer(raw_product_id)
                quantity = positive_integer(item.get('quantity')) if isinstance(item, dict) else None
                if product_id and quantity:
                    self.items[str(product_id)] = {'quantity': quantity}
        if self.items != stored_items:
            self._save()

    def __iter__(self):
        product_ids = [int(product_id) for product_id in self.items]

        products = Product.objects.filter(pk__in=product_ids).select_related('category')
        products_by_id = {str(product.pk): product for product in products}

        for product_id, stored in self.items.items():
            product = products_by_id.get(str(product_id))
            quantity = positive_integer(stored.get('quantity'))
            if product is None or quantity is None:
                continue
            yield {
                'product': product,
                'quantity': quantity,
                'line_total': product.price * quantity,
            }

    def __len__(self):
        total = 0
        for item in self.items.values():
            quantity = positive_integer(item.get('quantity'))
            if quantity:
                total += quantity
        return total

    @property
    def subtotal(self):
        """Sum of all products before discounts."""
        return sum((item['line_total'] for item in self), Decimal('0.00'))

    @property
    def discount_percent(self):
        """Tiered discount: >2500 -> 5%, >5000 -> 10%."""
        st = self.subtotal
        if st > DISCOUNT_THRESHOLD_TIER2:
            return DISCOUNT_PERCENT_TIER2
        if st > DISCOUNT_THRESHOLD_TIER1:
            return DISCOUNT_PERCENT_TIER1
        return 0

    @property
    def discount_amount(self):
        """Calculated discount in UAH."""
        percent = self.discount_percent
        if not percent:
            return Decimal('0.00')
        return (self.subtotal * Decimal(percent) / Decimal('100')).quantize(Decimal('0.01'))

    @property
    def total(self):
        """Final total to pay after discount."""
        return self.subtotal - self.discount_amount

    @property
    def next_tier(self):
        """Information on how much UAH is needed to reach the next discount tier."""
        st = self.subtotal
        if st <= DISCOUNT_THRESHOLD_TIER1:
            needed = (DISCOUNT_THRESHOLD_TIER1 + Decimal('0.01')) - st
            return {
                'target': DISCOUNT_THRESHOLD_TIER1,
                'percent': DISCOUNT_PERCENT_TIER1,
                'needed': needed,
                'label': f'Додайте ще на {needed:.2f} ₴ для знижки 5%',
            }
        if st <= DISCOUNT_THRESHOLD_TIER2:
            needed = (DISCOUNT_THRESHOLD_TIER2 + Decimal('0.01')) - st
            return {
                'target': DISCOUNT_THRESHOLD_TIER2,
                'percent': DISCOUNT_PERCENT_TIER2,
                'needed': needed,
                'label': f'Додайте ще на {needed:.2f} ₴ для максимальної знижки 10%',
            }
        return None

    def quantity_for(self, product_id):
        parsed_id = positive_integer(product_id)
        if parsed_id is None:
            return 0
        return positive_integer(self.items.get(str(parsed_id), {}).get('quantity')) or 0

    def add(self, product, quantity):
        quantity = positive_integer(quantity)
        if quantity is None or quantity > MAX_CART_QUANTITY:
            raise ValueError('Cart quantity must be between 1 and 999.')
        product_id = str(product.pk)
        new_quantity = self.quantity_for(product.pk) + quantity
        if new_quantity > MAX_CART_QUANTITY:
            raise ValueError('A product cannot exceed 999 units in the cart.')
        self.items[product_id] = {'quantity': new_quantity}
        self._save()

    def update(self, product_id, quantity):
        parsed_id = positive_integer(product_id)
        quantity = positive_integer(quantity)
        if parsed_id is None or quantity is None or quantity > MAX_CART_QUANTITY:
            raise ValueError('Cart quantity must be between 1 and 999.')
        self.items[str(parsed_id)] = {'quantity': quantity}
        self._save()

    def remove(self, product_id):
        self.items.pop(str(product_id), None)
        self._save()

    def _save(self):
        self.session[self.session_key] = self.items
        self.session.modified = True
