import logging
from django.conf import settings


class RequireDevelTrue(logging.Filter):
    def filter(self, record):
        return settings.DEVEL
