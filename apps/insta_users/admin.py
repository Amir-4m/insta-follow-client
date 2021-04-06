from django.contrib import admin, messages

from apps.insta_users.models import InstaUser
from apps.insta_users.utils.instagram import instagram_login
from apps.insta_users.utils.insta_follow import insta_follow_register


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    list_display = ("username", "user_id")
    search_fields = ("username", "user_id")

    def save_model(self, request, obj, form, change):
        if obj.stats == InstaUser.STATUS_ACTIVE:
            # instagram login if has no session
            if obj.session is None or 'session_id' not in obj.session.keys():
                try:
                    instagram_login(obj, commit=False)
                except Exception as e:
                    messages.error(request, f'Instagram Login Failed! {e}')

            # register insta-follow if user has no server_key
            if obj.server_key is None:
                try:
                    insta_follow_register(obj, commit=False)
                except Exception as e:
                    messages.error(request, f'Insta-Follow Login Failed!{e}')

        super().save_model(request, obj, form, change)

