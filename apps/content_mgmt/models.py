from django.db import models
from django.utils.translation import ugettext_lazy as _


class Content(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)
    image_url = models.TextField(_('image url'))
    caption = models.TextField(_("caption"), default="")

    def __str__(self):
        return self.caption
