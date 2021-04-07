from django.db import models
from django.db.models import Count, Min
from django.utils.translation import ugettext_lazy as _


class Proxy(models.Model):
    ENABLE_STATUS = 'enable'
    DISABLE_STATUS = 'disable'
    STATUS_CHOICES = (
        (ENABLE_STATUS, _('enable')),
        (DISABLE_STATUS, _('disable')),
    )
    HTTP_PROTOCOL = 1
    HTTPS_PROTOCOL = 2
    PROTOCOL_CHOICES = (
        (HTTP_PROTOCOL, _('HTTP')),
        (HTTPS_PROTOCOL, _('HTTPS')),
    )

    protocol = models.PositiveSmallIntegerField(_('protocol'), choices=PROTOCOL_CHOICES)
    ip = models.CharField(_('IP'), max_length=120)
    port = models.PositiveSmallIntegerField(_('port'))

    username = models.CharField(_('username'), max_length=50, blank=True)
    password = models.CharField(_('password'), max_length=50, blank=True)

    status = models.CharField(_('status'), max_length=7, default=ENABLE_STATUS)

    def __str__(self):
        return f'{self.id}-{self.ip}'

    @staticmethod
    def get_low_traffic_proxy():
        try:
            return Proxy.objects.filter(
                status=Proxy.ENABLE_STATUS
            ).annotate(
                used_number=Count('instauser_proxy')
            ).order_by('used_number').values('used_number', 'id')[0]['id']
        except KeyError:
            return None

