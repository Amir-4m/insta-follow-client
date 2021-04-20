from django.contrib import admin

from .models import InstaImage, InstaVideo#, Sentence


@admin.register(InstaImage)
class InstaImageAdmin(admin.ModelAdmin):
    list_display = ('created_time', 'content_type', 'id', 'image')
    list_filter = ('content_type', 'categories')
    search_fields = ('id', 'image')
    filter_horizontal = ('categories',)


@admin.register(InstaVideo)
class InstaVideoAdmin(admin.ModelAdmin):
    list_display = ('created_time', 'id', 'video')
    list_filter = ('categories',)
    search_fields = ('id', 'video')
    filter_horizontal = ('categories',)


# @admin.register(Sentence)
# class SentenceAdmin(admin.ModelAdmin):
#     pass

