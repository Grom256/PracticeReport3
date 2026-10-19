from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('my-products/', views.ProductManageListView.as_view(), name='product_manage_list'),
    path('my-products/add/', views.ProductCreateView.as_view(), name='product_create'),
    path('my-products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('my-products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
]
