from django.db import models
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _


class Proxy(models.Model):
    PROTOCOL_HTTP = 'http'
    PROTOCOL_HTTPS = 'https'
    PROTOCOL_CHOICES = (
        (PROTOCOL_HTTP, _('HTTP')),
        (PROTOCOL_HTTPS, _('HTTPS')),
    )

    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    protocol = models.CharField(_('protocol'), max_length=5, choices=PROTOCOL_CHOICES)
    server = models.CharField(_('server'), max_length=120)
    port = models.PositiveSmallIntegerField(_('port'))

    username = models.CharField(_('username'), max_length=50, blank=True)
    password = models.CharField(_('password'), max_length=50, blank=True)

    is_enable = models.BooleanField(_('is enable'), default=True)

    class Meta:
        db_table = 'proxies'
        verbose_name_plural = _('proxies')

    def __str__(self):
        return f'{self.id}-{self.server}'

    @classmethod
    def get_proxy(cls):
        try:
            return cls.objects.filter(
                is_enable=True
            ).annotate(
                used_number=Count('insta_users')
            ).order_by('used_number').values('used_number', 'id')[0]['id']
        except KeyError:
            return None

