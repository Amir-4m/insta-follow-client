from datetime import datetime, timedelta

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from apps.proxies.models import Proxy


class InstaAction(object):
    ACTION_LIKE = 'L'
    ACTION_FOLLOW = 'F'
    ACTION_COMMENT = 'C'

    ACTION_CHOICES = (
        (ACTION_FOLLOW, 'follow'),
        (ACTION_LIKE, 'like'),
        (ACTION_COMMENT, 'comment'),
    )

    BLOCK_TYPE_TEMP = 'temp'
    BLOCK_TYPE_SPAM = 'spam'
    BLOCK_TYPE_PERM = 'perm'

    @classmethod
    def get_action_from_key(cls, key):
        for act in cls.ACTION_CHOICES:
            if key == act[0]:
                return act[1]


class InstaContentCategory(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)
    title = models.CharField(_('title'), max_length=64)

    class Meta:
        db_table = 'insta_categories'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.title


class LiveManager(models.Manager):

    def live(self):
        return super().get_queryset().filter(
            status=InstaUser.STATUS_ACTIVE,
            server_key__isnull=False,
        ).exclude(
            session='',
        )

    def new(self):
        return super().get_queryset().filter(
            status=InstaUser.STATUS_NEW,
        ).exclude(
            session='',
        )


class InstaUser(models.Model):
    STATUS_ACTIVE = 10
    STATUS_NEW = 11
    # STATUS_BLOCKED_TEMP = 20
    # STATUS_BLOCKED = 21
    STATUS_REMOVED = 30
    STATUS_DISABLED = 31
    STATUS_LOGIN_FAILED = 40
    STATUS_LOGIN_LIMIT = 41

    STATUS_CHOICES = (
        (STATUS_NEW, _("new")),
        (STATUS_ACTIVE, _("active")),
        (STATUS_REMOVED, _("removed")),
        (STATUS_DISABLED, _("disabled")),
        (STATUS_LOGIN_FAILED, _("login failed")),
        (STATUS_LOGIN_LIMIT, _("login limited")),
    )

    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    username = models.CharField(_("username"), max_length=64, unique=True)
    password = models.CharField(_("password"), max_length=128)
    user_id = models.PositiveBigIntegerField(_("user ID"), unique=True, blank=True, null=True)
    session = models.TextField(_("session"), blank=True)
    user_agent = models.TextField(_("user agent"), blank=True)
    proxy = models.ForeignKey('proxies.Proxy', on_delete=models.SET_NULL, null=True, blank=True, related_name='insta_users')

    server_key = models.UUIDField(_('server Key'), blank=True, null=True, help_text=_('insta follow server key'))

    status = models.PositiveSmallIntegerField(_("Status"), choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True)
    description = models.TextField(_("description"), blank=True)

    blocked_data = models.JSONField(_('blocked data'), default=dict, editable=False)

    categories = models.ManyToManyField(InstaContentCategory)

    objects = LiveManager()

    class Meta:
        db_table = 'insta_users'

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        self.username = self.username.lower()
        if self.user_id is None and self.session != '':
            self.user_id = self.get_session.get('ds_user_id', None)
        super().save(*args, **kwargs)

    def set_session_proxy(self, session):
        if self.proxy is None:
            self.set_proxy()
        session.proxies = {self.proxy.protocol: f'{self.proxy.server}:{self.proxy.port}'}

    def set_proxy(self):
        self.proxy_id = Proxy.get_proxy()

    def clear_session(self):
        self.session = ''
        self.proxy = None

    @staticmethod
    def generate_session_string_from_dict(cookie_dict):
        return "; ".join([str(x) + "=" + str(y) for x, y in cookie_dict.items()])

    def set_session(self, cookie_dict):
        self.session = self.generate_session_string_from_dict(cookie_dict)

    @property
    def get_session(self):
        if self.session:
            return dict([tuple(i.strip().split('=')) for i in self.session.split(';')])
        return dict()

    def set_blocked(self, action, block_type):
        block_count = min(self.blocked_data.get(action, {}).get('count', 0) + 1, settings.INSTA_FOLLOW_SETTINGS['max_lock'])
        self.blocked_data[action] = dict(
            block_time=int(datetime.now().timestamp()),
            block_time_display=datetime.now().strftime('%m-%d %H:%M'),
            block_type=block_type,
            count=block_count
        )

    def remove_blocked(self, action):
        if action in self.blocked_data:
            del self.blocked_data[action]
            self.save()

    def is_blocked(self, action):
        if action not in self.blocked_data:
            return False

        action_str = InstaAction.get_action_from_key(action)

        _data = self.blocked_data[action]
        if _data['block_type'] == InstaAction.BLOCK_TYPE_PERM:
            return True

        if _data['block_type'] == InstaAction.BLOCK_TYPE_TEMP:
            return _data['block_time'] > int((datetime.now() - timedelta(minutes=settings.INSTA_FOLLOW_SETTINGS[f'pre_lock_{action_str}'])).timestamp())

        if _data['block_type'] == InstaAction.BLOCK_TYPE_SPAM:
            return _data['block_time'] > int((datetime.now() - timedelta(minutes=_data['count'] * settings.INSTA_FOLLOW_SETTINGS[f'lock_{action_str}'])).timestamp())

        return True
