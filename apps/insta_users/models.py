from django.db import models
from django.utils.translation import ugettext_lazy as _


class InstaUser(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_BLOCKED = "blocked"
    STATUS_TEMPORARY_BLOCKED = "temporary blocked"
    STATUS_REMOVED = "removed"

    STATUS = ((STATUS_ACTIVE, _("active")),
              (STATUS_BLOCKED, _("blocked")),
              (STATUS_TEMPORARY_BLOCKED, _("temporary blocked")),
              (STATUS_REMOVED, _("removed")))

    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)
    username = models.CharField(_("username"), max_length=128)
    password = models.CharField(_("password"), max_length=128)
    user_id = models.BigIntegerField(_("user ID"), blank=True, null=True)
    session = models.JSONField(_("session"), blank=True, null=True)
    server_key = models.UUIDField(_('server Key'), blank=True, null=True)
    status = models.CharField(_("Status"), choices=STATUS, default=STATUS_ACTIVE, max_length=100)

    def __str__(self):
        return self.username
