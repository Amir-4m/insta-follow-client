from django.contrib import admin
from .models import Category, CaptionContent, ImageContent, VideoContent


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(CaptionContent)
class CaptionContentAdmin(admin.ModelAdmin):
    list_display = ('created_time',)


@admin.register(ImageContent)
class ImageContentAdmin(admin.ModelAdmin):
    list_display = ('created_time',)


@admin.register(VideoContent)
class VideoContentAdmin(admin.ModelAdmin):
    list_display = ('created_time',)
