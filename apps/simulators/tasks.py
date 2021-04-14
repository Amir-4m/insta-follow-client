import time
import random

from django.conf import settings

from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task

from apps.insta_users.models import InstaUser, InstaAction
from apps.insta_users.utils.instagram import get_instagram_suggested_follows, do_instagram_action

MAX_FOLLOW_EACH_TURN = 6


@shared_task()
def follow_suggested(insta_user_id):
    action = InstaAction.get_action_from_key(InstaAction.ACTION_FOLLOW)
    order = dict(action=InstaAction.ACTION_FOLLOW, id=0)
    insta_user = InstaUser.objects.get(user_id=insta_user_id)

    suggested_follows = get_instagram_suggested_follows(insta_user)[:MAX_FOLLOW_EACH_TURN]
    for data in suggested_follows:
        order['entity_id'] = data['node']['user']['id']
        try:
            do_instagram_action(insta_user, order)
        except Exception:
            break
        time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{action}"])


@shared_task()
def follow_new_user(insta_user_id):
    action = InstaAction.get_action_from_key(InstaAction.ACTION_FOLLOW)
    order = dict(action=InstaAction.ACTION_FOLLOW, entity_id=insta_user_id, id=0)

    active_users = InstaUser.objects.live().order_by('?')[:MAX_FOLLOW_EACH_TURN]
    for active_user in active_users:
        if active_user.is_blocked(InstaAction.ACTION_FOLLOW):
            continue
        try:
            do_instagram_action(active_user, order)
        except Exception:
            continue
        time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{action}"])


@periodic_task(run_every=crontab(minute='*/30'))
def random_follow_task():
    new_insta_user_ids = InstaUser.objects.new().filter(
        created_time__hour=random.randint(0, 24)
    ).values_list('user_id', flat=True)

    action_to_call = globals()[random.choice(('follow_suggested', 'follow_new_user'))]
    for insta_user_id in new_insta_user_ids:
        action_to_call.delay(insta_user_id)
