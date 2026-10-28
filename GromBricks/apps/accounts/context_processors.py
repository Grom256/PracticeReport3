from django.conf import settings


def store_links(request):
    return {'telegram_channel_url': settings.TELEGRAM_URL}
