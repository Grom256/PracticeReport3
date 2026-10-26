from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
    path('stock-notify/<int:product_id>/', views.stock_notification_subscribe, name='stock_notify'),
    path('telegram/sync/', views.sync_telegram_chat_id, name='telegram_sync'),
    path('my-products/', views.ProductManageListView.as_view(), name='product_manage_list'),
    path('my-products/add/', views.ProductCreateView.as_view(), name='product_create'),
    path('my-products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('my-products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
]
