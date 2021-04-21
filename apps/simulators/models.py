from django.db import models
from django.utils.translation import ugettext_lazy as _


class InstaContent(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    categories = models.ManyToManyField('insta_users.InstaContentCategory')

    class Meta:
        abstract = True


class InstaImageManager(models.Manager):

    def posts(self):
        return super().get_queryset().filter(content_type=InstaImage.TYPE_POST)

    def stories(self):
        return super().get_queryset().filter(content_type=InstaImage.TYPE_STORY)

    def profiles(self):
        return super().get_queryset().filter(content_type=InstaImage.TYPE_PROFILE)


class InstaImage(InstaContent):
    TYPE_POST = "post"
    TYPE_STORY = "story"
    TYPE_PROFILE = "profile"

    CONTENT_TYPE_CHOICES = (
        (TYPE_POST, _("post")),
        (TYPE_STORY, _("story")),
        (TYPE_PROFILE, _("profile")),
    )

    image = models.ImageField(_('image'), upload_to='images')
    caption = models.TextField(_('caption'), blank=True)

    content_type = models.CharField(_("type"), max_length=8, choices=CONTENT_TYPE_CHOICES, db_index=True)

    objects = InstaImageManager()

    class Meta:
        db_table = 'insta_images'
        verbose_name = _('Insta Image')
        verbose_name_plural = _('Insta Images')


class InstaVideo(InstaContent):
    video = models.FileField(_('video'), upload_to='videos')
    caption = models.TextField(_('caption'), blank=True)

    class Meta:
        db_table = 'insta_videos'
        verbose_name = _('Insta Video')
        verbose_name_plural = _('Insta Videos')


class Sentence(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    sentence = models.TextField(_('sentence'))

    def __str__(self):
        return f"{self.sentence[:20]}..."
