from django.db import models
from django.utils.translation import ugettext_lazy as _


class InstaAction(object):
    ACTION_LIKE = 'L'
    ACTION_FOLLOW = 'F'
    ACTION_COMMENT = 'C'

    ACTION_CHOICES = (
        (ACTION_LIKE, 'like'),
        (ACTION_FOLLOW, 'follow'),
        (ACTION_COMMENT, 'comment'),
    )


class LiveManager(models.Manager):

    def live(self):
        return super().get_queryset().filter(
            session__isnull=False,
            server_key__isnull=False,
            status=InstaUser.STATUS_ACTIVE,
        )


class InstaUser(models.Model):
    STATUS_ACTIVE = 10
    STATUS_BLOCKED_TEMP = 20
    STATUS_BLOCKED = 21
    STATUS_REMOVED = 30
    STATUS_WRONG = 40

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _("active")),
        (STATUS_BLOCKED, _("blocked")),
        (STATUS_BLOCKED_TEMP, _("blocked temporary")),
        (STATUS_REMOVED, _("removed")),
        (STATUS_WRONG, _("wrong credentials")),
    )

    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    username = models.CharField(_("username"), max_length=64)
    password = models.CharField(_("password"), max_length=128)
    user_id = models.PositiveBigIntegerField(_("user ID"), unique=True, blank=True, null=True)
    session = models.JSONField(_("session"), blank=True, null=True)

    status = models.PositiveSmallIntegerField(_("Status"), choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    server_key = models.UUIDField(_('server Key'), blank=True, null=True, help_text=_('insta follow server key'))
    # block_count = models.PositiveSmallIntegerField(_("block Count"), default=0)
    proxy = models.ForeignKey('proxies.Proxy', on_delete=models.SET_NULL, null=True, blank=True, related_name='insta_users')

    objects = LiveManager()

    class Meta:
        db_table = 'insta_users'

    def __str__(self):
        return self.username

    def set_proxy(self, session):
        if self.proxy is not None:
            session.proxies = {self.proxy.protocol: f'{self.proxy.server}:{self.proxy.port}'}
