from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def home(request):
    categories = Category.objects.filter(is_active=True)
    latest_products = (
        Product.objects.filter(
            is_active=True,
            category__is_active=True,
            stock_quantity__gt=0,
        )
        .select_related('category')
        .order_by('-created_at')[:4]
    )
    return render(
        request,
        'catalog/home.html',
        {
            'categories': categories[:1],
            'latest_products': latest_products,
        },
    )


def product_list(request):
    products = Product.objects.filter(
        is_active=True,
        category__is_active=True,
    ).select_related('category')

    query = request.GET.get('q', '').strip()
    product_type = request.GET.get('type', '')
    category_slug = request.GET.get('category', '')
    sort = request.GET.get('sort', 'newest')
    in_stock = request.GET.get('in_stock') == '1'
    rare_only = request.GET.get('rare') == '1'

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(sku__icontains=query)
            | Q(description__icontains=query)
            | Q(series__icontains=query)
        )

    valid_types = {choice for choice, _label in Product.ProductType.choices}
    if product_type in valid_types:
        products = products.filter(product_type=product_type)
    else:
        product_type = ''

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if in_stock:
        products = products.filter(stock_quantity__gt=0)

    if rare_only:
        products = products.filter(is_rare=True)

    sort_options = {
        'newest': '-created_at',
        'name': 'name',
        'price_asc': 'price',
        'price_desc': '-price',
    }
    products = products.order_by(sort_options.get(sort, '-created_at'))
    if sort not in sort_options:
        sort = 'newest'

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'catalog/product_list.html',
        {
            'page_obj': page_obj,
            'categories': Category.objects.filter(is_active=True),
            'query': query,
            'selected_type': product_type,
            'selected_category': category_slug,
            'selected_sort': sort,
            'in_stock': in_stock,
            'rare_only': rare_only,
            'product_types': Product.ProductType.choices,
        },
    )


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related('category'),
        pk=pk,
        is_active=True,
        category__is_active=True,
    )
    return render(request, 'catalog/product_detail.html', {'product': product})
