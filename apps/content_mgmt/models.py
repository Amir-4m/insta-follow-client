from django.db import models
from django.utils.translation import ugettext_lazy as _


class Category(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)
    title = models.CharField(_('title'), max_length=64)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.title


class ImageContent(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)
    image = models.ImageField(_('image'), upload_to='images')

    categories = models.ManyToManyField(Category, related_name='images')


class VideoContent(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)
    title = models.CharField(_('title'), max_length=64)
    video = models.FileField(_('video'), upload_to='videos')

    categories = models.ManyToManyField(Category, related_name='videos')


class CaptionContent(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)
    caption = models.TextField(_('caption'))

    categories = models.ManyToManyField(Category, related_name='contents')
