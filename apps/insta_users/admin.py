from django.contrib import admin, messages

from .models import InstaUser
from ..proxies.models import Proxy
from .utils.instagram import instagram_login
from .utils.insta_follow import get_insta_follow_uuid


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    list_display = ("username", "user_id", "status", "proxy")
    search_fields = ("username", "user_id")
    raw_id_fields = ['proxy']

    def save_model(self, request, obj, form, change):
        if obj.status == InstaUser.STATUS_ACTIVE:
            if obj.session is None:
                try:
                    instagram_login(obj, commit=False)
                except Exception as e:
                    messages.error(request, f'Instagram Login Failed! {e}')

            if obj.session and obj.server_key is None:
                obj.server_key = get_insta_follow_uuid(obj)

            if obj.proxy is None:
                obj.proxy_id = Proxy.get_proxy()

        super().save_model(request, obj, form, change)
