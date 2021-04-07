from django.contrib import admin, messages

from apps.insta_users.models import InstaUser
from apps.insta_users.utils.instagram import instagram_login
from apps.insta_users.utils.insta_follow import get_insta_follow_uuid


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    list_display = ("username", "user_id")
    search_fields = ("username", "user_id")

    def save_model(self, request, obj, form, change):
        if obj.stats == InstaUser.STATUS_ACTIVE:
            if obj.session is None:
                try:
                    instagram_login(obj, commit=False)
                except Exception as e:
                    messages.error(request, f'Instagram Login Failed! {e}')

            if obj.session and obj.server_key is None:
                obj.server_key = get_insta_follow_uuid(obj)

        super().save_model(request, obj, form, change)

