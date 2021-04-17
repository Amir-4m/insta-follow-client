from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import InstaUser, InstaContentCategory


@admin.register(InstaContentCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_time')


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    list_display = ("username", "created_time", "updated_time", "user_id", "status", "blocked", "proxy", "server_key")
    list_filter = ("status", "created_time")
    search_fields = ("username", "user_id")
    raw_id_fields = ('proxy',)
    filter_horizontal = ('categories',)
    readonly_fields = ('blocked_data',)
    actions = ('make_active', 'make_disable')

    @admin.display
    def blocked(self, obj):
        return ', '.join(obj.blocked_data.keys())

    @admin.action(description=_('Mark selected as Active.'))
    def make_active(self, request, queryset):
        queryset.update(status=InstaUser.STATUS_ACTIVE)

    @admin.action(description=_('Mark selected as Disabled.'))
    def make_disable(self, request, queryset):
        queryset.update(status=InstaUser.STATUS_DISABLED)
