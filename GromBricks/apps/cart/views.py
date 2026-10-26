from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.catalog.models import Product

from .cart import MAX_CART_QUANTITY, Cart
from .forms import CartQuantityForm


@login_required
def cart_detail(request):
    cart = Cart(request)
    items = list(cart)
    return render(
        request,
        'cart/cart_detail.html',
        {
            'cart': cart,
            'items': items,
            'subtotal': cart.subtotal,
            'discount_percent': cart.discount_percent,
            'discount_amount': cart.discount_amount,
            'total': cart.total,
            'next_tier': cart.next_tier,
        },
    )


@login_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(
        Product,
        pk=product_id,
        is_active=True,
        category__is_active=True,
    )
    cart = Cart(request)
    current_quantity = cart.quantity_for(product.pk)
    available_quantity = min(MAX_CART_QUANTITY, product.stock_quantity - current_quantity)
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('catalog:product_detail', kwargs={'pk': product.pk})
    if available_quantity < 1:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'У кошику вже максимальна доступна кількість цього товару.'}, status=400)
        messages.error(request, 'У кошику вже максимальна доступна кількість цього товару.')
        return redirect(next_url)

    form = CartQuantityForm(request.POST, max_quantity=available_quantity)
    if not form.is_valid():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Вкажи коректну кількість товару.'}, status=400)
        messages.error(request, 'Вкажи коректну кількість товару.')
        return redirect(next_url)

    quantity = form.cleaned_data['quantity']
    cart.add(product, quantity)
    messages.success(request, f'«{product.name}» додано до кошика.')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        count = sum(item['quantity'] for item in cart)
        return JsonResponse({
            'status': 'ok',
            'message': f'«{product.name}» додано до кошика.',
            'cart_count': count,
        })

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
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
    form = CartQuantityForm(request.POST, max_quantity=product.stock_quantity)
    if not form.is_valid():
        messages.error(request, 'Вкажи кількість не менше одного.')
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
