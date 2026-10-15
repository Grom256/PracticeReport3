from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import Product

from .cart import Cart
from .forms import CartQuantityForm


@login_required
def cart_detail(request):
    cart = Cart(request)
    items = list(cart)
    total = sum((item['line_total'] for item in items), Decimal('0.00'))
    return render(request, 'cart/cart_detail.html', {'items': items, 'total': total})


@login_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(
        Product,
        pk=product_id,
        is_active=True,
        category__is_active=True,
    )
    form = CartQuantityForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Вкажи коректну кількість товару.')
        return redirect('catalog:product_detail', pk=product.pk)

    cart = Cart(request)
    quantity = form.cleaned_data['quantity']
    if cart.quantity_for(product.pk) + quantity > product.stock_quantity:
        messages.error(request, 'У кошик не можна додати більше товару, ніж є на складі.')
    else:
        cart.add(product, quantity)
        messages.success(request, f'«{product.name}» додано до кошика.')
    return redirect('catalog:product_detail', pk=product.pk)


@login_required
@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    if cart.quantity_for(product_id) < 1:
        messages.error(request, 'Цього товару вже немає у кошику.')
        return redirect('cart:detail')

    product = get_object_or_404(
        Product,
        pk=product_id,
        is_active=True,
        category__is_active=True,
    )
    form = CartQuantityForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Вкажи кількість не менше одного.')
    elif form.cleaned_data['quantity'] > product.stock_quantity:
        messages.error(request, 'Запитана кількість перевищує залишок на складі.')
    else:
        cart.update(product.pk, form.cleaned_data['quantity'])
        messages.success(request, 'Кількість товару оновлено.')
    return redirect('cart:detail')


@login_required
@require_POST
def cart_remove(request, product_id):
    Cart(request).remove(product_id)
    messages.info(request, 'Товар видалено з кошика.')
    return redirect('cart:detail')
