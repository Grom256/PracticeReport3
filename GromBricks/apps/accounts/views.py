from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, ProfileForm, RegistrationForm
from .models import Profile


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            Profile.objects.create(user=user)
        login(request, user)
        messages.success(request, 'Обліковий запис створено. Вітаємо у GromBricks!')
        return redirect('accounts:profile')

    return render(request, 'accounts/register.html', {'form': form})


class AccountLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


@require_POST
def account_logout(request):
    logout(request)
    messages.info(request, 'Ви вийшли з облікового запису.')
    return redirect('catalog:home')


@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, 'Дані профілю оновлено.')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'form': form})
