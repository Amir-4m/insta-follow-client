from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import Proxy


@admin.register(Proxy)
class ProxyAdmin(admin.ModelAdmin):
    list_display = ['server', 'port',  'protocol', 'is_enable']
    list_filter = ['is_enable']

    @admin.action(description=_('Mark selected as Enable.'))
    def make_enable(self, request, queryset):
        queryset.update(is_enable=True)

    @admin.action(description=_('Mark selected as Disabled.'))
    def make_disable(self, request, queryset):
        queryset.update(is_enable=False)
