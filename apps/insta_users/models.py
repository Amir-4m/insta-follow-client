from django.db import models
from django.utils.translation import ugettext_lazy as _


class InstaUser(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)
    username = models.CharField(_("username"), max_length=128)
    password = models.CharField(_("password"), max_length=128)
    user_id = models.BigIntegerField(_("user ID"), blank=True, null=True)
    session = models.TextField(_("session"), blank=True)

    def __str__(self):
        return self.username
