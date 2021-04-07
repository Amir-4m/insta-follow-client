from django.contrib import admin

from .models import Proxy


@admin.register(Proxy)
class ProxyAdmin(admin.ModelAdmin):
    list_display = ['ip', 'port',  'protocol', 'status']
    list_filter = ['status']

