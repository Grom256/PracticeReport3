import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import EmailVerificationForm, LoginForm, ProfileForm, RegistrationForm
from .models import Profile


def send_verification_email(user, code):
    subject = 'Код підтвердження електронної пошти — GromBricks'
    message = (
        f'Вітаємо, {user.first_name or user.username}!\n\n'
        f'Дякуємо за реєстрацію на сайті інтернет-магазину GromBricks.\n'
        f'Ваш одноразовий код підтвердження пошти: {code}\n\n'
        'Введіть його на сайті, щоб завершити створення акаунту.\n\n'
        'Якщо ви не реєструвалися у GromBricks, проігноруйте цей лист.'
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        code = f'{secrets.randbelow(900000) + 100000}'
        with transaction.atomic():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            Profile.objects.create(
                user=user,
                is_email_verified=False,
                verification_code=code,
            )

        try:
            send_verification_email(user, code)
        except Exception:
            pass

        request.session['verify_user_id'] = user.pk
        messages.info(
            request,
            f'На адресу {user.email} надіслано 6-значний код підтвердження.',
        )
        return redirect('accounts:verify_email')

    return render(request, 'accounts/register.html', {'form': form})


def verify_email(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    user_id = request.session.get('verify_user_id')
    if not user_id:
        messages.warning(request, 'Будь ласка, зареєструйтесь або увійдіть.')
        return redirect('accounts:register')

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        profile_obj = user.profile
    except (User.DoesNotExist, Profile.DoesNotExist):
        request.session.pop('verify_user_id', None)
        return redirect('accounts:register')

    if user.is_active and profile_obj.is_email_verified:
        request.session.pop('verify_user_id', None)
        login(request, user)
        return redirect('accounts:profile')

    form = EmailVerificationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        entered_code = form.cleaned_data['code']
        if entered_code == profile_obj.verification_code:
            with transaction.atomic():
                user.is_active = True
                user.save(update_fields=['is_active'])
                profile_obj.is_email_verified = True
                profile_obj.verification_code = ''
                profile_obj.save(update_fields=['is_email_verified', 'verification_code'])
            request.session.pop('verify_user_id', None)
            login(request, user)
            messages.success(request, 'Пошту успішно підтверджено! Вітаємо у GromBricks.')
            return redirect('accounts:profile')
        else:
            form.add_error('code', 'Невірний код підтвердження. Перевірте пошту та спробуйте ще раз.')

    return render(
        request,
        'accounts/verify_email.html',
        {
            'form': form,
            'user_email': user.email,
        },
    )


@require_POST
def resend_verification_code(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        messages.warning(request, 'Сесія підтвердження завершилася. Будь ласка, зареєструйтесь знову.')
        return redirect('accounts:register')

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        profile_obj = user.profile
    except (User.DoesNotExist, Profile.DoesNotExist):
        request.session.pop('verify_user_id', None)
        return redirect('accounts:register')

    code = f'{secrets.randbelow(900000) + 100000}'
    profile_obj.verification_code = code
    profile_obj.save(update_fields=['verification_code'])

    try:
        send_verification_email(user, code)
        messages.success(request, f'Новий код надіслано на вашу пошту {user.email}.')
    except Exception as exc:
        messages.error(request, f'Помилка відправки листа: {exc}')

    return redirect('accounts:verify_email')


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
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, 'Дані профілю оновлено.')
        return redirect('accounts:profile')

    recent_orders = (
        request.user.orders.prefetch_related('items__product')
        .order_by('-created_at')[:4]
    )
    total_orders = request.user.orders.count()

    return render(
        request,
        'accounts/profile.html',
        {
            'form': form,
            'profile': profile,
            'recent_orders': recent_orders,
            'total_orders': total_orders,
        },
    )
