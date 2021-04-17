import logging
import time
import random

from django.conf import settings

from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task

from .models import InstaContentImage
from apps.insta_users.models import InstaUser, InstaAction
from apps.insta_users.utils.instagram import get_instagram_suggested_follows, do_instagram_action, change_instagram_profile_pic, get_instagram_profile_posts

logger = logging.getLogger(__name__)

MAX_ACTION_EACH_TURN = 6


@shared_task()
def change_profile_picture(insta_user_id):
    insta_user = InstaUser.objects.get(user_id=insta_user_id)
    insta_user_categories = list(insta_user.categories.all())
    if not insta_user_categories:
        return

    category = random.choice(insta_user_categories)
    img = InstaContentImage.objects.filter(categories=category).order_by('?')[0]
    change_instagram_profile_pic(insta_user, img.image)


@shared_task()
def like_new_user_posts(insta_user_id):
    action = InstaAction.get_action_from_key(InstaAction.ACTION_LIKE)
    order = dict(action=InstaAction.ACTION_LIKE, id=0)
    insta_user = InstaUser.objects.get(user_id=insta_user_id)
    insta_user_posts = get_instagram_profile_posts(insta_user, insta_user.username)

    active_users = InstaUser.objects.live().exclude(blocked_data__has_key=InstaAction.ACTION_LIKE).order_by('?')[:MAX_ACTION_EACH_TURN]
    for active_user in active_users:
        # random_posts = [i["id"] for i in random.choices(insta_user_posts, k=min(1, len(insta_user_posts)//3))]
        random_posts = insta_user_posts
        for data in random_posts:
            order['entity_id'] = data['node']['id']
            try:
                do_instagram_action(active_user, order)
            except Exception as e:
                logger.warning(f"[Simulator like_new_user_posts]-[insta_user: {insta_user.username}]-[active_user: {active_user.username}]-[{type(e)}]-[err: {e}]")
                continue
            time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{action}"])


@shared_task()
def follow_suggested(insta_user_id):
    action = InstaAction.get_action_from_key(InstaAction.ACTION_FOLLOW)
    order = dict(action=InstaAction.ACTION_FOLLOW, id=0)
    insta_user = InstaUser.objects.get(user_id=insta_user_id)
    if insta_user.is_blocked(InstaAction.ACTION_FOLLOW):
        return

    suggested_follows = get_instagram_suggested_follows(insta_user)[:MAX_ACTION_EACH_TURN]
    for data in suggested_follows:
        order['entity_id'] = data['node']['user']['id']
        try:
            do_instagram_action(insta_user, order)
        except Exception as e:
            logger.warning(f"[Simulator follow_suggested]-[insta_user: {insta_user.username}]-[suggested: {order['entity_id']}]-[{type(e)}]-[err: {e}]")
            break
        time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{action}"])


@shared_task()
def follow_new_user(insta_user_id):
    action = InstaAction.get_action_from_key(InstaAction.ACTION_FOLLOW)
    order = dict(action=InstaAction.ACTION_FOLLOW, entity_id=insta_user_id, id=0)

    active_users = InstaUser.objects.live().exclude(blocked_data__has_key=InstaAction.ACTION_FOLLOW).order_by('?')[:MAX_ACTION_EACH_TURN]
    for active_user in active_users:
        try:
            do_instagram_action(active_user, order)
        except Exception as e:
            logger.warning(f'[Simulator follow_new_user]-[insta_user: {insta_user_id}]-[active_user: {active_user.username}]-[{type(e)}]-[err: {e}]')
            continue
        time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{action}"])


@shared_task()
def follow_active_users(insta_user_id):
    action = InstaAction.get_action_from_key(InstaAction.ACTION_FOLLOW)
    order = dict(action=InstaAction.ACTION_FOLLOW, id=0)
    insta_user = InstaUser.objects.get(user_id=insta_user_id)
    if insta_user.is_blocked(InstaAction.ACTION_FOLLOW):
        return

    active_users = InstaUser.objects.live().order_by('?')[:MAX_ACTION_EACH_TURN]
    for active_user in active_users:
        order['entity_id'] = active_user.user_id
        try:
            do_instagram_action(insta_user, order)
        except Exception as e:
            logger.warning(f'[Simulator follow_active_users]-[insta_user: {insta_user.username}]-[active_user: {active_user.username}]-[{type(e)}]-[err: {e}]')
            break
        time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{action}"])


@periodic_task(run_every=crontab(minute='*/30'))
def random_follow_task():
    new_insta_user_ids = InstaUser.objects.new().filter(
        # created_time__hour=random.randint(0, 24)
    ).values_list('user_id', flat=True).order_by('?')[:3]

    action_to_call = globals()[random.choice((
        'follow_suggested',
        'follow_new_user',
        'follow_active_users',
        'change_profile_picture',
    ))]
    for insta_user_id in new_insta_user_ids:
        action_to_call.delay(insta_user_id)
