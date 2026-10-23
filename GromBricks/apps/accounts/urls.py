from django.urls import path

from .views import (
    AccountLoginView,
    account_logout,
    profile,
    register,
    resend_verification_code,
    verify_email,
)

app_name = 'accounts'

urlpatterns = [
    path('register/', register, name='register'),
    path('verify-email/', verify_email, name='verify_email'),
    path('resend-code/', resend_verification_code, name='resend_code'),
    path('login/', AccountLoginView.as_view(), name='login'),
    path('logout/', account_logout, name='logout'),
    path('profile/', profile, name='profile'),
]
