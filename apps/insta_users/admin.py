from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from .models import InstaUser


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    list_display = ("username", "created_time", "updated_time", "user_id", "status", "blocked", "server_key")
    list_filter = ("status", "created_time")
    search_fields = ("username", "user_id")
    raw_id_fields = ('proxy',)
    readonly_fields = ('blocked_data',)
    actions = ('make_instauser_active',)

    @admin.display
    def blocked(self, obj):
        return ', '.join(obj.blocked_data.keys())

    @admin.action(description=_('Mark selected as Active.'))
    def make_instauser_active(self, request, queryset):
        queryset.update(status=InstaUser.STATUS_ACTIVE)

