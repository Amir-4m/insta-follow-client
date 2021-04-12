from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from .models import InstaUser


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    list_display = ("username", "created_time", "updated_time", "user_id", "status", "blocked", "server_key")
    list_filter = ("status", "created_time")
    actions = ['make_instauser_active']
    search_fields = ("username", "user_id")
    raw_id_fields = ['proxy']

    @admin.display
    def blocked(self, obj):
        return ', '.join(obj.blocked_data.keys())

    @admin.action(description=_('Mark selected insta users as Active.'))
    def make_instauser_active(self, request, queryset):
        queryset.update(status=InstaUser.STATUS_ACTIVE)

