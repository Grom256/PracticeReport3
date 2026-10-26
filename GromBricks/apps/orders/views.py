from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import Profile
from apps.cart.cart import MAX_CART_QUANTITY, Cart, positive_integer
from apps.catalog.models import Product

from .forms import OrderCheckoutForm
from .models import Order, OrderItem


def _cart_quantities(cart):
    """Return validated product ids and quantities from the session cart."""
    quantities = {}
    for product_id, item in cart.items.items():
        quantity = positive_integer(item.get('quantity')) if isinstance(item, dict) else None
        product_id = positive_integer(product_id)
        if product_id is None or quantity is None or quantity > MAX_CART_QUANTITY:
            return None
        if product_id in quantities:
            return None
        quantities[product_id] = quantity
    return quantities


@login_required
def checkout(request):
    cart = Cart(request)
    quantities = _cart_quantities(cart)
    if quantities is None:
        messages.error(request, 'Перевір кількість товарів у кошику: має бути від 1 до 999 шт. на позицію.')
        return redirect('cart:detail')
    if not quantities:
        messages.info(request, 'Додай товари до кошика перед оформленням замовлення.')
        return redirect('cart:detail')

    if request.method == 'POST':
        form = OrderCheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                products = list(
                    Product.objects.select_for_update()
                    .select_related('category')
                    .filter(pk__in=quantities)
                    .order_by('pk')
                )
                products_by_id = {product.pk: product for product in products}

                unavailable = len(products_by_id) != len(quantities)
                insufficient_stock = False
                for product_id, quantity in quantities.items():
                    product = products_by_id.get(product_id)
                    if product is None or not product.is_active or not product.category.is_active:
                        unavailable = True
                    elif quantity > product.stock_quantity:
                        insufficient_stock = True

                if unavailable or insufficient_stock:
                    if unavailable:
                        messages.error(
                            request,
                            'Один із товарів більше недоступний. Перевір кошик і спробуй знову.',
                        )
                    if insufficient_stock:
                        messages.error(
                            request,
                            'Кількість товару на складі змінилася. Онови кошик перед оформленням.',
                        )
                    return redirect('cart:detail')

                order = form.save(commit=False)
                order.user = request.user
                order.payment_method = Order.PaymentMethod.CASH_ON_DELIVERY
                order.subtotal = cart.subtotal
                order.discount_percent = cart.discount_percent
                order.discount_amount = cart.discount_amount
                order.total_amount = cart.total
                order.save()

                order_items = []
                products_to_update = []
                for product_id, quantity in quantities.items():
                    product = products_by_id[product_id]
                    order_items.append(
                        OrderItem(
                            order=order,
                            product=product,
                            quantity=quantity,
                            unit_price=product.price,
                        )
                    )
                    product.stock_quantity -= quantity
                    product.updated_at = timezone.now()
                    products_to_update.append(product)

                OrderItem.objects.bulk_create(order_items)
                Product.objects.bulk_update(products_to_update, ('stock_quantity', 'updated_at'))
                request.session.pop(Cart.session_key, None)
                request.session.modified = True

            messages.success(request, f'Замовлення №{order.pk} оформлено.')
            return redirect('orders:detail', pk=order.pk)
    else:
        initial = {'recipient_name': request.user.get_full_name()}
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = None
        if profile and profile.phone:
            initial['phone'] = profile.phone
        form = OrderCheckoutForm(initial=initial)

    cart_items = list(cart)
    return render(
        request,
        'orders/checkout.html',
        {
            'form': form,
            'cart': cart,
            'cart_items': cart_items,
            'subtotal': cart.subtotal,
            'discount_percent': cart.discount_percent,
            'discount_amount': cart.discount_amount,
            'total': cart.total,
        },
    )


@login_required
def order_list(request):
    line_total = ExpressionWrapper(
        F('items__quantity') * F('items__unit_price'),
        output_field=DecimalField(max_digits=20, decimal_places=2),
    )
    orders = Order.objects.filter(user=request.user).annotate(
        calculated_total=Coalesce(
            Sum(line_total),
            Value(Decimal('0.00')),
            output_field=DecimalField(max_digits=20, decimal_places=2),
        )
    )
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.filter(user=request.user).prefetch_related('items__product'),
        pk=pk,
    )
    return render(request, 'orders/order_detail.html', {'order': order})
