import re

from django.core.exceptions import ValidationError


SKU_PATTERN = re.compile(r'^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$')


def validate_product_sku(value):
    """Allow Latin letters and digits, with optional single hyphens between groups."""
    if not SKU_PATTERN.fullmatch(value):
        raise ValidationError(
            'Артикул може містити лише латинські літери, цифри та дефіси між ними.',
            code='invalid_product_sku',
        )
