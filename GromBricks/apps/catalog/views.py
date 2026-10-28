from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ProductForm, StockNotificationForm
from .models import Category, Product, StockNotification, WishlistItem
from .services import (
    send_telegram_message,
    sync_telegram_chat_id_from_updates,
)


def home(request):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        related = (
            Product.objects.filter(
                is_active=True,
                category=self.object.category,
            )
            .exclude(pk=self.object.pk)
            .select_related('category')[:4]
        )
        if not related.exists():
            related = (
                Product.objects.filter(is_active=True)
                .exclude(pk=self.object.pk)
                .select_related('category')[:4]
            )
        context['related_products'] = related

        user = self.request.user
        context['is_in_wishlist'] = (
            user.is_authenticated
            and WishlistItem.objects.filter(user=user, product=self.object).exists()
        )

        initial = {}
        if user.is_authenticated:
            initial['email'] = user.email
            if hasattr(user, 'profile') and user.profile.telegram_chat_id:
                initial['telegram_chat_id'] = user.profile.telegram_chat_id
                initial['channel'] = StockNotification.Channel.BOTH
            else:
                initial['channel'] = StockNotification.Channel.EMAIL

        context['notification_form'] = StockNotificationForm(initial=initial)
        context['bot_username'] = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'GromBricksBot')

        context['has_stock_subscription'] = False
        if user.is_authenticated:
            context['has_stock_subscription'] = StockNotification.objects.filter(
                user=user,
                product=self.object,
                is_notified=False,
            ).exists()

        return context


@login_required
def wishlist_view(request):
    """Display user's wishlist."""
    items = (
        WishlistItem.objects.filter(user=request.user)
        .select_related('product__category')
        .order_by('-created_at')
    )
    initial_notification = {}
    if request.user.email:
        initial_notification['email'] = request.user.email
    if hasattr(request.user, 'profile') and request.user.profile.telegram_chat_id:
        initial_notification['telegram_chat_id'] = request.user.profile.telegram_chat_id

    notification_form = StockNotificationForm(initial=initial_notification)
    bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'GromBricksBot')

    return render(
        request,
        'catalog/wishlist.html',
        {
            'items': items,
            'notification_form': notification_form,
            'bot_username': bot_username,
        },
    )


@login_required
@require_POST
def wishlist_toggle(request, product_id):
    """Add or remove product from wishlist (via form submit or AJAX)."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        item.delete()
        added = False
        msg = f'«{product.name}» видалено зі списку бажань.'
        messages.info(request, msg)
    else:
        added = True
        msg = f'«{product.name}» додано до списку бажань.'
        messages.success(request, msg)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'status': 'ok',
            'added': added,
            'message': msg,
            'wishlist_count': request.user.wishlist_items.count(),
        })

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse_lazy('catalog:wishlist')
    return redirect(next_url)


@require_POST
def stock_notification_subscribe(request, product_id):
    """Subscribe to out-of-stock product notification via Email or Telegram."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    form = StockNotificationForm(request.POST)

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if not form.is_valid():
        first_error = next(iter(form.errors.values()))[0] if form.errors else 'Перевірте введені дані.'
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': first_error}, status=400)
        messages.error(request, first_error)
        return redirect('catalog:product_detail', pk=product.pk)

    channel = form.cleaned_data['channel']
    email = form.cleaned_data['email']
    telegram_chat_id = form.cleaned_data['telegram_chat_id']

    sub, _created = StockNotification.objects.get_or_create(
        product=product,
        user=request.user if request.user.is_authenticated else None,
        email=email,
        telegram_chat_id=telegram_chat_id,
        defaults={'channel': channel, 'is_notified': False},
    )
    if not _created:
        sub.channel = channel
        sub.is_notified = False
        sub.save(update_fields=['channel', 'is_notified'])

    # If user provided telegram_chat_id and profile exists without one, remember it
    if request.user.is_authenticated and hasattr(request.user, 'profile') and telegram_chat_id:
        if not request.user.profile.telegram_chat_id:
            request.user.profile.telegram_chat_id = telegram_chat_id
            request.user.profile.save(update_fields=['telegram_chat_id'])

    # Send a confirmation ping to Telegram if Telegram was chosen
    if channel in (StockNotification.Channel.TELEGRAM, StockNotification.Channel.BOTH) and telegram_chat_id:
        send_telegram_message(
            telegram_chat_id,
            f'✅ <b>Ви підписалися на сповіщення про наявність!</b>\n\n'
            f'Товар: <b>{product.name}</b>\n'
            f'Ми надішлемо вам повідомлення сюди, щойно він надійде на склад GromBricks ⚡️'
        )

    success_msg = f'Ви успішно підписалися на сповіщення про появу «{product.name}»!'
    messages.success(request, success_msg)

    if is_ajax:
        return JsonResponse({'status': 'ok', 'message': success_msg})

    return redirect('catalog:product_detail', pk=product.pk)


@login_required
@require_POST
def sync_telegram_chat_id(request):
    """Helper view to detect user's Telegram Chat ID from @GromBricksBot updates."""
    chat_id = sync_telegram_chat_id_from_updates(request.user)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if chat_id:
        msg = f'Telegram успішно підключено! (ID: {chat_id})'
        messages.success(request, msg)
        if is_ajax:
            return JsonResponse({'status': 'ok', 'chat_id': chat_id, 'message': msg})
    else:
        msg = 'Повідомлень не знайдено. Перейдіть у бот @GromBricksBot, натисніть /start та натисніть перевірку ще раз.'
        messages.warning(request, msg)
        if is_ajax:
            return JsonResponse({'status': 'not_found', 'message': msg}, status=404)

    return redirect('accounts:profile')


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_staff

class ProductManageListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = 'catalog/product_manage_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.filter(owner=self.request.user).select_related('category')


class ProductCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_message = 'Товар створено.'

    def get_success_url(self):
        return reverse_lazy('catalog:product_manage_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnedProductMixin(StaffRequiredMixin):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'

    def get_queryset(self):
        return Product.objects.filter(owner=self.request.user).select_related('category')


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
