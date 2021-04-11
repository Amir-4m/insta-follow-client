from django.db import models
from django.utils.translation import ugettext_lazy as _


class ProfilePicture(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)
    profile_picture = models.ImageField(_('profile Picture'), blank=True, upload_to='media/profile_pics')


class PostPicture(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)
    post_picture = models.ImageField(_('profile Picture'), blank=True, upload_to='media/post_pics')
