from django.contrib import admin
from .models import PostPicture, ProfilePicture


@admin.register(PostPicture)
class PostPictureAdmin(admin.ModelAdmin):
    list_display = ('created_time',)


@admin.register(ProfilePicture)
class ProfilePictureAdmin(admin.ModelAdmin):
    list_display = ('created_time',)
