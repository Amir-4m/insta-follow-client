from django.db import models
from django.utils.translation import ugettext_lazy as _


class InstaUser(models.Model):
    STATUS_ACTIVE = 10
    STATUS_BLOCKED_TEMP = 20
    STATUS_BLOCKED = 21
    STATUS_REMOVED = 30

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _("active")),
        (STATUS_BLOCKED, _("blocked")),
        (STATUS_BLOCKED_TEMP, _("blocked temporary")),
        (STATUS_REMOVED, _("removed"))
    )

    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    username = models.CharField(_("username"), max_length=64)
    password = models.CharField(_("password"), max_length=128)
    user_id = models.PositiveBigIntegerField(_("user ID"), unique=True, blank=True, null=True)
    session = models.JSONField(_("session"), blank=True, null=True)

    server_key = models.UUIDField(_('server Key'), blank=True, null=True)

    status = models.PositiveSmallIntegerField(_("Status"), choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)

    def __str__(self):
        return self.username
