from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.helpers import ActionForm
from django import forms

from .models import InstaUser, InstaContentCategory, InstaAction


class RemoveBlockActionForm(ActionForm):
    action_unblock = forms.ChoiceField(
        choices=InstaAction.ACTION_CHOICES, help_text=_('to remove block for selected action'))


class FollowBlockFilter(admin.SimpleListFilter):
    title = _('follow block')
    parameter_name = 'f_b'

    def lookups(self, request, model_admin):
        return (1, _('yes')), (2, _('no'))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(blocked_data__has_key=InstaAction.ACTION_FOLLOW)
        if self.value() == '2':
            return queryset.exclude(blocked_data__has_key=InstaAction.ACTION_FOLLOW)
        return queryset


class LikeBlockFilter(admin.SimpleListFilter):
    title = _('like block')
    parameter_name = 'l_b'

    def lookups(self, request, model_admin):
        return (1, _('yes')), (2, _('no'))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(blocked_data__has_key=InstaAction.ACTION_LIKE)
        if self.value() == '2':
            return queryset.exclude(blocked_data__has_key=InstaAction.ACTION_LIKE)
        return queryset


class CommentBlockFilter(admin.SimpleListFilter):
    title = _('comment block')
    parameter_name = 'c_b'

    def lookups(self, request, model_admin):
        return (1, _('yes')), (2, _('no'))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(blocked_data__has_key=InstaAction.ACTION_COMMENT)
        if self.value() == '2':
            return queryset.exclude(blocked_data__has_key=InstaAction.ACTION_COMMENT)
        return queryset


@admin.register(InstaContentCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_time')


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    action_form = RemoveBlockActionForm
    list_display = ("username", "created_time", "updated_time", "user_id", "status", "blocked", "proxy", "server_key")
    list_filter = ("status", "created_time", FollowBlockFilter, LikeBlockFilter, CommentBlockFilter)
    search_fields = ("username", "user_id")
    raw_id_fields = ('proxy',)
    filter_horizontal = ('categories',)
    readonly_fields = ('blocked_data',)

    def get_actions(self, request):
        self.actions = ('make_active', 'make_disable')

        if request.user.is_superuser:
            self.actions = ('make_active', 'make_disable', 'remove_block')
        return super().get_actions(request)

    @admin.display
    def blocked(self, obj):
        return ', '.join(obj.blocked_data.keys())

    @admin.action(description=_('Mark selected as Active.'))
    def make_active(self, request, queryset):
        queryset.update(status=InstaUser.STATUS_ACTIVE)

    @admin.action(description=_('Mark selected as Disabled.'))
    def make_disable(self, request, queryset):
        queryset.update(status=InstaUser.STATUS_DISABLED)

    @admin.action(description=_('Remove block for selected users.'))
    def remove_block(self, request, queryset):
        for q in queryset:
            q.remove_blocked(request.POST.get('action_unblock'))
