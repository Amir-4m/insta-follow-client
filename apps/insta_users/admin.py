from django.contrib import admin

from .models import InstaUser


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    list_display = ("username", "created_time", "updated_time", "user_id", "status", "blocked", "server_key")
    list_filter = ("status", "created_time")
    search_fields = ("username", "user_id")
    raw_id_fields = ['proxy']

    @admin.display
    def blocked(self, obj):
        return ', '.join(obj.blocked_data.keys())
