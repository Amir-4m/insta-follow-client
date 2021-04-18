from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.helpers import ActionForm
from django import forms

from .models import InstaUser, InstaContentCategory, InstaAction


class RemoveBlockActionForm(ActionForm):
    action_unblock = forms.ChoiceField(
        choices=InstaAction.ACTION_CHOICES, help_text=_('to remove block for selected action'))


@admin.register(InstaContentCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_time')


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    action_form = RemoveBlockActionForm
    list_display = ("username", "created_time", "updated_time", "user_id", "status", "blocked", "proxy", "server_key")
    list_filter = ("status", "created_time")
    search_fields = ("username", "user_id")
    raw_id_fields = ('proxy',)
    filter_horizontal = ('categories',)
    readonly_fields = ('blocked_data',)
    actions = ('make_active', 'make_disable', 'remove_block')

    @admin.display
    def blocked(self, obj):
        return ', '.join(obj.blocked_data.keys())

    @admin.action(description=_('Mark selected as Active.'))
    def make_active(self, request, queryset):
        queryset.update(status=InstaUser.STATUS_ACTIVE)

    @admin.action(description=_('Mark selected as Disabled.'))
    def make_disable(self, request, queryset):
        queryset.update(status=InstaUser.STATUS_DISABLED)

    @admin.action(description=_('Remove selected block.'))
    def remove_block(self, request, queryset):
        for q in queryset:
            q.remove_blocked(request.POST.get('action_unblock'))
