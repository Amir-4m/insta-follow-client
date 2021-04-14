import time
from datetime import timedelta

from django.utils import timezone

from celery.schedules import crontab
from celery.task import periodic_task

from apps.insta_users.models import InstaUser
from apps.insta_users.utils.instagram import get_instagram_session
from .utils import follow, follow_suggested


@periodic_task(run_every=crontab(hour=2))
def follow_new_fake_users_task():
    active_users = InstaUser.objects.filter(status=InstaUser.STATUS_ACTIVE).order_by('?')[:6]

    to_follow_users = InstaUser.objects.filter(status=InstaUser.STATUS_NEW)
    for user in to_follow_users:
        for a_user in active_users:
            time.sleep(.6)
            follow(get_instagram_session(a_user), user.user_id)


@periodic_task(run_every=crontab(hour=4))
def follow_suggested_user_task():
    users = InstaUser.objects.filter(status=InstaUser.STATUS_NEW)
    for user in users:
        follow_suggested(user)

    InstaUser.objects.filter(
        created_time__gte=timezone.now() - timedelta(days=1)
    ).update(status=InstaUser.STATUS_ACTIVE)
