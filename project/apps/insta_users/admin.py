from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.helpers import ActionForm
from django import forms


from .models import InstaUser, InstaContentCategory, InstaAction


class RemoveBlockActionForm(ActionForm):
    unblock = forms.ChoiceField(
        choices=InstaAction.ACTION_CHOICES,
        help_text=_('to remove block for selected action')
    )


class GeneralFilter(admin.SimpleListFilter):

    def lookups(self, request, model_admin):
        return (1, _('Yes')), (2, _('No'))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(**self.filter_params)
        if self.value() == '2':
            return queryset.exclude(**self.filter_params)
        return queryset


class HasSessionFilter(GeneralFilter):
    title = _('has Session')
    parameter_name = 'ss'

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.exclude(session='')
        if self.value() == '2':
            return queryset.filter(session='')
        return queryset


class HasServerKeyFilter(GeneralFilter):
    title = _('has Server Key')
    parameter_name = 'sk'

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(server_key__isnull=False)
        if self.value() == '2':
            return queryset.filter(server_key__isnull=True)
        return queryset


class FollowBlockFilter(GeneralFilter):
    title = _('block Follow')
    parameter_name = 'f_b'
    filter_params = dict(blocked_data__has_key=InstaAction.ACTION_FOLLOW)


class LikeBlockFilter(GeneralFilter):
    title = _('block Like')
    parameter_name = 'l_b'
    filter_params = dict(blocked_data__has_key=InstaAction.ACTION_LIKE)


class CommentBlockFilter(GeneralFilter):
    title = _('block Comment')
    parameter_name = 'c_b'
    filter_params = dict(blocked_data__has_key=InstaAction.ACTION_COMMENT)


class UserIdFilter(GeneralFilter):
    title = _('has user id')
    parameter_name = 'u_i'

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.exclude(user_id=None)
        if self.value() == '2':
            return queryset.filter(user_id=None)
        return queryset


@admin.register(InstaContentCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_time')


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    action_form = RemoveBlockActionForm
    list_display = (
        "username", "created_time", "updated_time", "user_id", "manage_content", "status", "blocked", "has_session", "has_server_key", "fake_user", "user_activity")
    list_filter = ("status", "manage_content", "fake_user", UserIdFilter, HasSessionFilter, HasServerKeyFilter, FollowBlockFilter, LikeBlockFilter,
                   CommentBlockFilter)
    date_hierarchy = "created_time"
    search_fields = ("username", "user_id")
    raw_id_fields = ('proxy',)
    filter_horizontal = ('categories',)
    readonly_fields = ('blocked_data',)

    def user_activity(self, obj):
        actions = {1: "Addition", 2: "Change", 3: "Deletion"}
        log = LogEntry.objects.filter(object_id=obj.id).last()
        if log:
            return f"{log.user}--{actions[log.action_flag]}"

        return None

    def get_actions(self, request):
        self.actions = ('make_active',)

        if request.user.is_superuser:
            self.actions = ('make_active', 'make_new', 'clear_session', 'remove_block', 'manage_true', 'manage_false')
        return super().get_actions(request)

    @admin.display
    def blocked(self, obj):
        return ', '.join(obj.blocked_data.keys())

    @admin.display(boolean=True)
    def has_session(self, obj):
        return obj.session != ''

    @admin.display(boolean=True)
    def has_server_key(self, obj):
        return obj.server_key is not None

    @admin.action(description=_('Clear Session for selected users.'))
    def clear_session(self, request, queryset):
        queryset.update(session='', user_agent='', proxy=None, blocked_data={})

    @admin.action(description=_('Mark selected as ACTIVE.'))
    def make_active(self, request, queryset):
        queryset.update(status=InstaUser.STATUS_ACTIVE)

    @admin.action(description=_('Mark selected as NEW.'))
    def make_new(self, request, queryset):
        queryset.update(status=InstaUser.STATUS_NEW)

    @admin.action(description=_('Remove block for selected users.'))
    def remove_block(self, request, queryset):
        for q in queryset:
            q.remove_blocked(request.POST.get('unblock'))

    @admin.action(description=_('Change manage content to True'))
    def manage_true(self, request, queryset):
        queryset.update(manage_content=True)

    @admin.action(description=_('Change manage content to False'))
    def manage_false(self, request, queryset):
        queryset.update(manage_content=False)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'

    list_filter = [
        'user',
        'content_type',
        'action_flag',
    ]

    search_fields = [
        'object_repr',
        'change_message',
        'user'
    ]

    list_display = [
        'action_time',
        'user',
        'content_type',
        'action_flag',
    ]

    class Media:
        pass
