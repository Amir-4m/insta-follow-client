from django.contrib import admin

from .models import Proxy


@admin.register(Proxy)
class ProxyAdmin(admin.ModelAdmin):
    list_display = ['server', 'port',  'protocol', 'is_enable']
    list_filter = ['is_enable']

