from django.db import models
from django.db.models import Count, Min
from django.utils.translation import ugettext_lazy as _


class Proxy(models.Model):
    HTTP_PROTOCOL = 1
    HTTPS_PROTOCOL = 2
    PROTOCOL_CHOICES = (
        (HTTP_PROTOCOL, _('HTTP')),
        (HTTPS_PROTOCOL, _('HTTPS')),
    )

    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    protocol = models.PositiveSmallIntegerField(_('protocol'), choices=PROTOCOL_CHOICES)
    server = models.CharField(_('server'), max_length=120)
    port = models.PositiveSmallIntegerField(_('port'))

    username = models.CharField(_('username'), max_length=50, blank=True)
    password = models.CharField(_('password'), max_length=50, blank=True)

    is_enable = models.BooleanField(_('is enable'), default=True)

    def __str__(self):
        return f'{self.id}-{self.server}'

    @staticmethod
    def get_low_traffic_proxy():
        try:
            return Proxy.objects.filter(
                is_enable=True
            ).annotate(
                used_number=Count('instauser_proxy')
            ).order_by('used_number').values('used_number', 'id')[0]['id']
        except KeyError:
            return None

