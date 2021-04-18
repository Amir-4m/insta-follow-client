from django.contrib import admin
from .models import InstaContentCaption, InstaContentImage, InstaContentVideo, InstaStoryImage, InstaProfileImage


@admin.register(InstaContentCaption)
class CaptionContentAdmin(admin.ModelAdmin):
    list_display = ('created_time', 'id', 'caption')
    list_filter = ('categories',)
    search_fields = ('id', 'caption')
    filter_horizontal = ('categories',)


@admin.register(InstaContentImage)
class ImageContentAdmin(admin.ModelAdmin):
    list_display = ('created_time', 'id', 'image')
    list_filter = ('categories',)
    search_fields = ('id', 'image')
    filter_horizontal = ('categories',)


@admin.register(InstaContentVideo)
class VideoContentAdmin(admin.ModelAdmin):
    list_display = ('created_time', 'id', 'video')
    list_filter = ('categories',)
    search_fields = ('id', 'video')
    filter_horizontal = ('categories',)


@admin.register(InstaStoryImage)
class StoryImageAdmin(admin.ModelAdmin):
    list_display = ('created_time', 'id', 'image')
    list_filter = ('categories',)
    search_fields = ('id', 'image')
    filter_horizontal = ('categories',)


@admin.register(InstaProfileImage)
class ProfileImageAdmin(admin.ModelAdmin):
    list_display = ('created_time', 'id', 'image')
    list_filter = ('categories',)
    search_fields = ('id', 'image')
    filter_horizontal = ('categories',)
