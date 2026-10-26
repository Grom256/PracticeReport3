import json
import logging
import urllib.parse
import urllib.request
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id: str, text: str) -> bool:
    """Send an HTML-formatted message to a user via Telegram Bot API."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token or not chat_id:
        logger.warning('Telegram token or chat_id is missing: token=%s, chat_id=%s', bool(token), chat_id)
        return False

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': str(chat_id).strip(),
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False,
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return bool(res_data.get('ok'))
    except Exception as exc:
        logger.error('Failed to send Telegram message to %s: %s', chat_id, exc)
        return False


def sync_telegram_chat_id_from_updates(user) -> str:
    """Check recent Telegram bot updates to auto-link user's chat_id if they sent /start."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token:
        return ''

    url = f'https://api.telegram.org/bot{token}/getUpdates'
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if not res_data.get('ok'):
                return ''
            updates = res_data.get('result', [])
            # Only the deep-link payload generated for this user may link a chat.
            expected_start_command = f'/start user_{user.pk}'
            for update in reversed(updates):
                msg = update.get('message', {})
                text = msg.get('text', '').strip()
                chat = msg.get('chat', {})
                chat_id = str(chat.get('id', ''))

                if not chat_id:
                    continue

                if text == expected_start_command:
                    profile = user.profile
                    profile.telegram_chat_id = chat_id
                    profile.save(update_fields=['telegram_chat_id'])
                    # Send friendly confirmation to Telegram
                    send_telegram_message(
                        chat_id,
                        f'👋 <b>Вітаємо у GromBricks!</b>\n\n'
                        f'Ваш акаунт <b>@{user.username}</b> успішно прив’язано до сповіщень про наявність товарів ⚡️'
                    )
                    return chat_id
    except Exception as exc:
        logger.error('Error syncing Telegram updates: %s', exc)

    return ''


def send_stock_email(email: str, product) -> bool:
    """Send stock availability notification via email."""
    if not email:
        return False

    subject = f'⚡️ Товар «{product.name}» знову в наявності! — GromBricks'
    message = (
        f'Чудова новина!\n\n'
        f'Товар, на який ви підписалися, знову з’явився на складі GromBricks:\n'
        f'«{product.name}» (Артикул: {product.sku})\n'
        f'Ціна: {product.price} ₴\n'
        f'Кількість в наявності: {product.stock_quantity} шт.\n\n'
        f'Встигніть оформити замовлення, поки товар не розібрали!\n'
        f'Переглянути товар: http://127.0.0.1:8000{product.get_absolute_url()}\n\n'
        f'З повагою,\nКоманда GromBricks'
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as exc:
        logger.error('Failed to send stock email to %s: %s', email, exc)
        return False


def process_stock_notifications(product) -> int:
    """Process all pending stock notifications for a given product."""
    notifications = product.stock_notifications.filter(is_notified=False)
    count = 0
    now = timezone.now()

    for item in notifications:
        sent = False
        # Email channel
        if item.channel in ('email', 'both'):
            target_email = item.email or (item.user.email if item.user else '')
            if target_email:
                if send_stock_email(target_email, product):
                    sent = True

        # Telegram channel
        if item.channel in ('telegram', 'both'):
            target_chat_id = item.telegram_chat_id or (
                item.user.profile.telegram_chat_id if item.user and hasattr(item.user, 'profile') else ''
            )
            if target_chat_id:
                tg_text = (
                    f'⚡️ <b>Товар знову у наявності в GromBricks!</b>\n\n'
                    f'<b>{product.name}</b>\n'
                    f'📦 Артикул: <code>{product.sku}</code>\n'
                    f'💰 Ціна: <b>{product.price} ₴</b>\n'
                    f'🔢 Доступно: <b>{product.stock_quantity} шт.</b>\n\n'
                    f'👉 <a href="http://127.0.0.1:8000{product.get_absolute_url()}">Переглянути та замовити на сайті</a>'
                )
                if send_telegram_message(target_chat_id, tg_text):
                    sent = True

        if sent:
            item.is_notified = True
            item.notified_at = now
            item.save(update_fields=['is_notified', 'notified_at'])
            count += 1

    return count
