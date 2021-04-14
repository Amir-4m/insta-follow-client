import logging
import os
import time
import random

from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

from celery.schedules import crontab
from celery.task import periodic_task
from celery import shared_task

from pid import PidFile

from .models import InstaUser, InstaAction
from .utils.insta_follow import get_insta_follow_uuid, insta_follow_get_orders, insta_follow_order_done
from .utils.instagram import instagram_login, do_instagram_action, InstagramMediaClosed

logger = logging.getLogger(__name__)

INSTA_USER_LOCK_KEY = "insta_lock_%s"

# TODO: for later use
"""
INSTAGRAM_HEADERS = {
    "Host": "www.instagram.com",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.instagram.com/accounts/edit/",
    "X-IG-App-ID": "936619743392459",
    "X-Requested-With": "XMLHttpRequest",
    "DNT": "1",
    "Connection": "keep-alive",
}
"""


def check_running(function_name):
    if not os.path.exists('/tmp'):
        os.mkdir('/tmp')
    file_lock = PidFile(str(function_name), piddir='/tmp')
    file_lock.create()
    return file_lock


def stop_duplicate_task(func):
    def inner_function():
        try:
            file_lock = check_running(func.__name__)
        except:
            logger.error(f"[Another {func.__name__} is already running]")
            return

        func()

        if file_lock:
            file_lock.close()

    return inner_function


# @periodic_task(run_every=crontab(minute='*/5'))
# def p_insta_user_action():
#     insta_user_action()


# @stop_duplicate_task
@periodic_task(run_every=crontab(minute='*/10'))
def insta_user_action():
    insta_users = InstaUser.objects.live()
    for insta_user in insta_users:

        action_selected = random.choice(InstaAction.ACTION_CHOICES[:-1])
        action = action_selected[1]

        if insta_user.is_blocked(action_selected[0]):
            logger.debug(f'skipping insta_user: {insta_user.username}, action {action} blocked')
            continue

        _ck = INSTA_USER_LOCK_KEY % insta_user.id
        if cache.get(_ck):
            logger.debug(f'skipping insta_user: {insta_user.username}, action {action} cache locked')
            continue

        orders = insta_follow_get_orders(insta_user, action)
        logger.debug(f'retrieved {len(orders)} - {[o["id"] for o in orders]} - for user: {insta_user.username}')

        cache.set(_ck, True, 300)
        do_orders.delay(insta_user.id, orders, action)


@shared_task
def do_orders(insta_user_id, orders, action):
    insta_user = InstaUser.objects.select_related('proxy').get(id=insta_user_id)
    all_done = []
    for order in orders:
        try:
            do_instagram_action(insta_user, order)
        except InstagramMediaClosed as e:
            insta_follow_order_done(insta_user, order['id'], check=True)
        except Exception:
            all_done.append(False)
            break
        else:
            insta_follow_order_done(insta_user, order['id'])
            all_done.append(True)
        time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{action}"])

    if all(all_done):
        insta_user.remove_blocked(action)

    cache.delete(INSTA_USER_LOCK_KEY % insta_user_id)


@shared_task
def insta_follow_login_task(insta_user_id):
    insta_user = InstaUser.objects.get(id=insta_user_id)
    insta_user.server_key = get_insta_follow_uuid(insta_user)
    insta_user.save()


@shared_task
def instagram_login_task(insta_user_id):
    insta_user = InstaUser.objects.get(id=insta_user_id)
    instagram_login(insta_user)


@periodic_task(run_every=crontab(minute='*'))
def activate_insta_users():
    no_session_users = InstaUser.objects.filter(
        status=InstaUser.STATUS_ACTIVE,
        session='',
    ).values_list('id', flat=True)

    for insta_user_id in no_session_users:
        instagram_login_task.delay(insta_user_id)

    no_uuid_users = InstaUser.objects.filter(
        status=InstaUser.STATUS_ACTIVE,
        server_key__isnull=True,
    ).exclude(session='').values_list('id', flat=True)

    for insta_user_id in no_uuid_users:
        insta_follow_login_task.delay(insta_user_id)

    InstaUser.objects.filter(
        Q(status=InstaUser.STATUS_DISABLED, updated_time__lt=timezone.now() - timezone.timedelta(days=3)) |
        Q(status=InstaUser.STATUS_LOGIN_LIMIT, updated_time__lt=timezone.now() - timezone.timedelta(hours=3))
    ).update(
        status=InstaUser.STATUS_ACTIVE,
    )
