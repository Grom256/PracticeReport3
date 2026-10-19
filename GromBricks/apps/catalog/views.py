from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ProductForm
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


class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        products = Product.objects.filter(
            is_active=True,
            category__is_active=True,
        ).select_related('category')

        self.query = self.request.GET.get('q', '').strip()
        self.product_type = self.request.GET.get('type', '')
        self.category_slug = self.request.GET.get('category', '')
        self.sort = self.request.GET.get('sort', 'newest')
        self.in_stock = self.request.GET.get('in_stock') == '1'
        self.rare_only = self.request.GET.get('rare') == '1'

        if self.query:
            products = products.filter(
                Q(name__icontains=self.query)
                | Q(sku__icontains=self.query)
                | Q(description__icontains=self.query)
                | Q(series__icontains=self.query)
            )

        valid_types = {choice for choice, _label in Product.ProductType.choices}
        if self.product_type in valid_types:
            products = products.filter(product_type=self.product_type)
        else:
            self.product_type = ''

        if self.category_slug:
            products = products.filter(category__slug=self.category_slug)
        if self.in_stock:
            products = products.filter(stock_quantity__gt=0)
        if self.rare_only:
            products = products.filter(is_rare=True)

        sort_options = {
            'newest': '-created_at',
            'name': 'name',
            'price_asc': 'price',
            'price_desc': '-price',
        }
        if self.sort not in sort_options:
            self.sort = 'newest'
        return products.order_by(sort_options[self.sort])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'categories': Category.objects.filter(is_active=True),
                'query': self.query,
                'selected_type': self.product_type,
                'selected_category': self.category_slug,
                'selected_sort': self.sort,
                'in_stock': self.in_stock,
                'rare_only': self.rare_only,
                'product_types': Product.ProductType.choices,
            }
        )
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.select_related('category').filter(
            is_active=True,
            category__is_active=True,
        )


class ProductManageListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'catalog/product_manage_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'owner')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(owner=self.request.user)


class ProductCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_message = 'Товар створено.'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('catalog:product_manage_list')


class OwnedProductMixin(LoginRequiredMixin):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'

    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'owner')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(owner=self.request.user)


class ProductUpdateView(OwnedProductMixin, SuccessMessageMixin, UpdateView):
    success_message = 'Зміни товару збережено.'

    def get_success_url(self):
        return reverse_lazy('catalog:product_manage_list')


class ProductDeleteView(OwnedProductMixin, DeleteView):
    template_name = 'catalog/product_confirm_delete.html'
    success_url = reverse_lazy('catalog:product_manage_list')

    def form_valid(self, form):
        messages.success(self.request, 'Товар видалено.')
        return super().form_valid(form)
