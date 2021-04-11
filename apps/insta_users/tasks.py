import logging
import os
import time

from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

from celery.schedules import crontab
from celery.task import periodic_task
from celery import shared_task

from pid import PidFile

from .models import InstaUser, InstaAction
from .utils.insta_follow import get_insta_follow_uuid, insta_follow_get_orders, insta_follow_order_done
from .utils.instagram import instagram_login, do_instagram_action

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
@periodic_task(run_every=crontab(minute='*'))
def insta_user_action():
    insta_users = InstaUser.objects.live()
    for insta_user in insta_users:

        _ck = INSTA_USER_LOCK_KEY % insta_user.id
        if cache.get(_ck):
            logger.debug(f'skipping insta_user: {insta_user.username}')
            continue

        action = InstaAction.get_action_from_key(InstaAction.ACTION_FOLLOW)
        orders = insta_follow_get_orders(insta_user, action)
        logger.debug(f'retrieved {len(orders)} - {[o["id"] for o in orders]} - for user: {insta_user.username}')

        cache.set(_ck, True, 300)
        do_orders.delay(insta_user.id, orders)


@shared_task
def do_orders(insta_user_id, orders):

    insta_user = InstaUser.objects.select_related('proxy').get(id=insta_user_id)
    if insta_user.status != insta_user.STATUS_ACTIVE:
        logger.debug(f'insta_user: {insta_user.username} is not active!')
        return

    for order in orders:
        try:
            do_instagram_action(insta_user, order)
        except:
            break
        else:
            insta_follow_order_done(insta_user, order['id'])
        time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{InstaAction.get_action_from_key(order['action'])}"])

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


@periodic_task(run_every=crontab(minute='*/10'))
def reactivate_blocked_users():
    reactivated = 0

    reactivated += InstaUser.objects.filter(
        status=InstaUser.STATUS_BLOCKED_TEMP,
        updated_time__lt=timezone.now() - timezone.timedelta(minutes=settings.INSTA_FOLLOW_SETTINGS['pre_lock_time'])
    ).update(
        status=InstaUser.STATUS_ACTIVE
    )

    # reactivated += InstaUser.objects.filter(
    #     status=InstaUser.STATUS_BLOCKED,
    #     updated_time__lt=timezone.now() - timezone.timedelta(minutes=settings.INSTA_FOLLOW_SETTINGS['lock_time'])
    # ).update(
    #     status=InstaUser.STATUS_ACTIVE
    # )

    return reactivated
