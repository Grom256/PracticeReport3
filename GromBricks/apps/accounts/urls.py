from django.urls import path

from .views import AccountLoginView, account_logout, profile, register

app_name = 'accounts'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', AccountLoginView.as_view(), name='login'),
    path('logout/', account_logout, name='logout'),
    path('profile/', profile, name='profile'),
]
