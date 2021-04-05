from django.contrib import admin
from apps.insta_users.models import InstaUser


@admin.register(InstaUser)
class InstaUserAdmin(admin.ModelAdmin):
    list_display = ("username", "user_id")
    search_fields = ("username", "user_id")
