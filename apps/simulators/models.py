from django.db import models
from django.utils.translation import ugettext_lazy as _


class InstaContent(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    categories = models.ManyToManyField('insta_users.InstaContentCategory')

    class Meta:
        abstract = True


class InstaContentImage(InstaContent):
    image = models.ImageField(_('image'), upload_to='images')

    class Meta:
        db_table = 'insta_images'
        verbose_name = _('Insta Image')
        verbose_name_plural = _('Insta Images')


class InstaContentVideo(InstaContent):
    video = models.FileField(_('video'), upload_to='videos')

    class Meta:
        db_table = 'insta_videos'
        verbose_name = _('Insta Video')
        verbose_name_plural = _('Insta Videos')


class InstaContentCaption(InstaContent):
    caption = models.TextField(_('caption'))

    class Meta:
        db_table = 'insta_captions'
        verbose_name = _('Insta Caption')
        verbose_name_plural = _('Insta Captions')


class InstaProfileImage(InstaContent):
    image = models.ImageField(_('image'), upload_to='profile_images')

    class Meta:
        db_table = 'insta_profile_images'
        verbose_name = _('Insta Profile Image')
        verbose_name_plural = _('Insta Profile Images')


class InstaStoryImage(InstaContent):
    image = models.ImageField(_('image'), upload_to='story_images')

    class Meta:
        db_table = 'insta_story_images'
        verbose_name = _('Insta Story Image')
        verbose_name_plural = _('Insta Story Images')
