import logging
import time
import random

from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

from celery.schedules import crontab
from celery.task import periodic_task
from celery import shared_task

from fake_useragent import UserAgent

from .models import InstaUser, InstaAction
from .utils.insta_follow import get_insta_follow_uuid, insta_follow_get_orders, insta_follow_order_done, insta_follow_test_user_upadte
from .utils.instagram import instagram_login, do_instagram_action, get_instagram_session, InstagramMediaClosed, INSTAGRAM_BASE_URL
from .utils.selenium import SeleniumService

logger = logging.getLogger(__name__)

INSTA_USER_LOCK_KEY = "insta_lock_%s"

ua = UserAgent()


@periodic_task(run_every=crontab(minute='*/4'))
def insta_user_action():
    insta_users = InstaUser.objects.live()
    for insta_user in insta_users:

        action_selected = random.choice(InstaAction.ACTION_CHOICES[:-2])
        action_key = action_selected[0]
        action_str = action_selected[1]

        if insta_user.is_blocked(action_key):
            logger.debug(f'skipping insta_user: {insta_user.username}, action {action_str} blocked')
            continue

        _ck = INSTA_USER_LOCK_KEY % insta_user.id
        if cache.get(_ck):
            logger.debug(f'skipping insta_user: {insta_user.username}, action {action_str} cache locked')
            continue

        orders = insta_follow_get_orders(insta_user, action_str)
        logger.debug(f'retrieved {len(orders)} - {[o["id"] for o in orders]} - for user: {insta_user.username}')

        cache.set(_ck, True, 300)
        do_orders.delay(insta_user.id, orders, action_key)


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
        time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{InstaAction.get_action_from_key(action)}"])

    if all(all_done):
        insta_user.remove_blocked(action)

    cache.delete(INSTA_USER_LOCK_KEY % insta_user_id)


@shared_task
def insta_follow_login_task(insta_user_id):
    insta_user = InstaUser.objects.get(id=insta_user_id)
    insta_user.server_key = get_insta_follow_uuid(insta_user)
    insta_user.save()


@shared_task
def insta_follow_update_task(insta_user_id):
    insta_user = InstaUser.objects.get(id=insta_user_id)
    insta_follow_test_user_upadte(insta_user)


@shared_task(queue='instagram_login_selenium')
def instagram_login_task(insta_user_id):
    insta_user = InstaUser.objects.get(id=insta_user_id)
    # instagram_login(insta_user)
    user_agent = ua.random
    session_cookie = SeleniumService(user_agent).get_instagram_session_id(insta_user.username, insta_user.password)
    if session_cookie:
        insta_user.session = session_cookie
        insta_user.user_agent = user_agent
        insta_user.set_proxy()
    else:
        insta_user.status = InstaUser.STATUS_LOGIN_FAILED

    insta_user.save()

    cache.delete(INSTA_USER_LOCK_KEY % insta_user_id)


@periodic_task(run_every=crontab(minute='*'))
def activate_insta_users():
    no_session_users = InstaUser.objects.filter(
        status=InstaUser.STATUS_NEW,
        session='',
    ).values_list('id', flat=True)[:2]

    for insta_user_id in no_session_users:
        _ck = INSTA_USER_LOCK_KEY % insta_user_id
        if cache.get(_ck):
            continue
        cache.set(_ck, True, 600)
        instagram_login_task.delay(insta_user_id)

    no_uuid_users = InstaUser.objects.filter(
        status=InstaUser.STATUS_ACTIVE,
        server_key__isnull=True,
    ).exclude(session='').values_list('id', flat=True)

    for insta_user_id in no_uuid_users:
        insta_follow_login_task.delay(insta_user_id)
        insta_follow_update_task.delay(insta_user_id)

    # make Active Insta User which been blocked to NEW for simulator
    InstaUser.objects.filter(
        status=InstaUser.STATUS_ACTIVE,
        session='',
    ).update(
        status=InstaUser.STATUS_NEW,
        updated_time=timezone.now()
    )

    # Re-Active Insta User after simulator works
    InstaUser.objects.filter(
        status=InstaUser.STATUS_NEW,
        updated_time__lt=timezone.now() - timezone.timedelta(days=2)
    ).exclude(
        session=''
    ).update(
        status=InstaUser.STATUS_ACTIVE,
        updated_time=timezone.now()
    )


@periodic_task(run_every=crontab(minute='*/15'))
def reactivate_disabled_insta_users():
    return InstaUser.objects.filter(
        Q(status=InstaUser.STATUS_DISABLED, updated_time__lt=timezone.now() - timezone.timedelta(days=3)) |
        Q(status=InstaUser.STATUS_LOGIN_LIMIT, updated_time__lt=timezone.now() - timezone.timedelta(hours=3))
    ).update(
        status=InstaUser.STATUS_ACTIVE
    )


@periodic_task(run_every=crontab(minute='0', hour='0'))
def cleanup_disabled_insta_users():
    InstaUser.objects.filter(
        Q(status=InstaUser.STATUS_DISABLED) | Q(status=InstaUser.STATUS_LOGIN_FAILED),
        updated_time__lt=timezone.now() - timezone.timedelta(days=3)
    ).update(status=InstaUser.STATUS_REMOVED)

    # TODO: uncomment
    # insta_users = InstaUser.objects.filter(
    #     status=InstaUser.STATUS_REMOVED,
    #     updated_time__lt=timezone.now() - timezone.timedelta(days=10)
    # )
    # for insta_user in insta_users:
    #     if insta_user.session:
    #         session = get_instagram_session(insta_user)
    #         link = f"{INSTAGRAM_BASE_URL}/{insta_user.username}/?__a=1"
    #         _s = session.get(link)
    #         should_be_deleted = _s.status_code == "404"
    #     else:
    #         should_be_deleted = True
    #
    #     if should_be_deleted:
    #         logger.info(f"{insta_user.username} deleted!!")
    #         insta_user.delete()
