from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

from apps.cart.cart import Cart
from apps.catalog.models import Product

from .forms import CheckoutForm
from .models import Order, OrderItem


class StockChanged(Exception):
    """The stock changed between adding an item and confirming checkout."""


@login_required
def checkout(request):
    cart = Cart(request)
    cart_items = list(cart)
    if not cart_items:
        messages.info(request, 'Додай товари до кошика перед оформленням замовлення.')
        return redirect('cart:detail')

    form = CheckoutForm(request.POST or None, user=request.user)
    total = sum((item['line_total'] for item in cart_items), Decimal('0.00'))

    if request.method == 'POST' and form.is_valid():
        requested = {item['product'].pk: item['quantity'] for item in cart_items}
        try:
            with transaction.atomic():
                locked_products = Product.objects.select_for_update().select_related(
                    'category'
                ).filter(pk__in=requested)
                products = {product.pk: product for product in locked_products}

                if len(products) != len(requested):
                    raise StockChanged
                for product_id, quantity in requested.items():
                    product = products[product_id]
                    if (
                        not product.is_active
                        or not product.category.is_active
                        or product.stock_quantity < quantity
                    ):
                        raise StockChanged

                order = form.save(commit=False)
                order.user = request.user
                order.save()
                for product_id, quantity in requested.items():
                    product = products[product_id]
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=product.price,
                    )
                    product.stock_quantity -= quantity
                    product.save(update_fields=['stock_quantity', 'updated_at'])
        except StockChanged:
            messages.error(
                request,
                'Залишок одного з товарів змінився. Перевір кошик і спробуй ще раз.',
            )
            return redirect('cart:detail')

        cart.clear()
        messages.success(request, f'Замовлення №{order.pk} створено.')
        return redirect('orders:detail', pk=order.pk)

    return render(
        request,
        'orders/checkout.html',
        {'form': form, 'cart_items': cart_items, 'total': total},
    )


@login_required
def order_list(request):
    amount_expression = ExpressionWrapper(
        F('items__quantity') * F('items__unit_price'),
        output_field=DecimalField(max_digits=20, decimal_places=2),
    )
    orders = Order.objects.filter(user=request.user).annotate(
        calculated_total=Coalesce(
            Sum(amount_expression),
            Value(Decimal('0.00'), output_field=DecimalField(max_digits=20, decimal_places=2)),
        )
    )
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        pk=pk,
        user=request.user,
    )
    return render(request, 'orders/order_detail.html', {'order': order})
