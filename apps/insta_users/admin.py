from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.helpers import ActionForm
from django import forms

from .models import InstaUser, InstaContentCategory, InstaAction


class RemoveBlockActionForm(ActionForm):
    unblock = forms.ChoiceField(
        choices=InstaAction.ACTION_CHOICES,
        help_text=_('to remove block for selected action')
    )


class BlockFilter(admin.SimpleListFilter):

    def lookups(self, request, model_admin):
        return (1, _('Yes')), (2, _('No'))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(blocked_data__has_key=self.action)
        if self.value() == '2':
            return queryset.exclude(blocked_data__has_key=self.action)
        return queryset


class FollowBlockFilter(BlockFilter):
    title = _('follow block')
    parameter_name = 'f_b'
    action = InstaAction.ACTION_FOLLOW


class LikeBlockFilter(BlockFilter):
    title = _('like block')
    parameter_name = 'l_b'
    action = InstaAction.ACTION_LIKE


class CommentBlockFilter(BlockFilter):
    title = _('comment block')
    parameter_name = 'c_b'
    action = InstaAction.ACTION_COMMENT


@admin.register(InstaContentCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_time')


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    action_form = RemoveBlockActionForm
    list_display = ("username", "created_time", "updated_time", "user_id", "status", "blocked", "proxy", "server_key")
    list_filter = ("status", FollowBlockFilter, LikeBlockFilter, CommentBlockFilter)
    date_hierarchy = "created_time"
    search_fields = ("username", "user_id")
    raw_id_fields = ('proxy',)
    filter_horizontal = ('categories',)
    readonly_fields = ('blocked_data',)

    def get_actions(self, request):
        self.actions = ('make_active', )

        if request.user.is_superuser:
            self.actions = ('make_active', 'make_new', 'remove_block')
        return super().get_actions(request)

    @admin.display
    def blocked(self, obj):
        return ', '.join(obj.blocked_data.keys())

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
