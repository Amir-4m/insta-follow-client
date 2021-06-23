import logging
import time
import random

from django.conf import settings

from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task

from .models import InstaImage, Sentence
from apps.insta_users.models import InstaUser, InstaAction
from apps.insta_users.utils.instagram import (
    get_instagram_session, do_instagram_action,
    get_instagram_suggested_follows, get_instagram_profile_posts,
    has_instagram_profile_picture, change_instagram_profile_pic,
    upload_instagram_post, upload_instagram_story,
    INSTAGRAM_USER_AGENT
)

# from utils.images import resize_image

logger = logging.getLogger(__name__)

MAX_ACTION_EACH_TURN = 3


# def make_random_sentence():
#     nouns = ["puppy", "car", "rabbit", "girl", "monkey"]
#     verbs = ["runs", "hits", "jumps", "drives", "barfs"]
#     adv = ["crazily.", "dutifully.", "foolishly.", "merrily.", "occasionally."]
#     adj = ["adorable", "clueless", "dirty", "odd", "stupid"]
#
#     _l = (nouns, verbs, adj, adv)
#
#     return ' '.join([random.choice(i) for i in _l])


@shared_task()
def change_profile_picture(insta_user_id):
    insta_user = InstaUser.objects.get(user_id=insta_user_id)
    insta_user_categories = list(insta_user.categories.all())
    if not insta_user_categories:
        return

    category = random.choice(insta_user_categories)
    content = InstaImage.objects.profiles().filter(categories=category).order_by('?')[0]
    try:
        session = get_instagram_session(insta_user)
        if has_instagram_profile_picture(insta_user, session) is False:
            logger.debug(
                f"[Simulator change_profile_picture]-[insta_user: {insta_user.username}]-[content: {content.id}]")
            change_instagram_profile_pic(insta_user, content.image, session)
    except Exception as e:
        logger.warning(f"[Simulator change_profile_picture]-[insta_user: {insta_user.username}]-[{type(e)}]-[err: {e}]")


@shared_task()
def upload_new_user_post(insta_user_id):
    insta_user = InstaUser.objects.get(user_id=insta_user_id)
    insta_user_categories = list(insta_user.categories.all())
    if not insta_user_categories:
        logger.warning(f"[Simulator upload_new_user_post - no category]-[insta_user: {insta_user.username}]")
        return

    category = random.choice(insta_user_categories)
    content = InstaImage.objects.posts().filter(categories=category).order_by('?')[0]

    # image = content.image
    # if image.width != image.height:
    #     image, image_bytes = resize_image(image)

    try:
        logger.debug(f"[Simulator upload_new_user_post]-[insta_user: {insta_user.username}]-[content: {content.id}]")
        session = get_instagram_session(insta_user, set_proxy=True, user_agent=INSTAGRAM_USER_AGENT)
        upload_instagram_post(session, content.image, content.caption)
    except Exception as e:
        logger.warning(f"[Simulator upload_new_user_post]-[insta_user: {insta_user.username}]-[{type(e)}]-[err: {e}]")


@shared_task()
def upload_new_user_story(insta_user_id):
    insta_user = InstaUser.objects.get(user_id=insta_user_id)
    insta_user_categories = list(insta_user.categories.all())
    if not insta_user_categories:
        return

    category = random.choice(insta_user_categories)
    content = InstaImage.objects.stories().filter(categories=category).order_by('?')[0]
    try:
        logger.debug(f"[Simulator upload_new_user_story]-[insta_user: {insta_user.username}]-[content: {content.id}]")
        session = get_instagram_session(insta_user, set_proxy=True, user_agent=INSTAGRAM_USER_AGENT)
        upload_instagram_story(session, content.image)
    except Exception as e:
        logger.warning(f"[Simulator upload_new_user_story]-[insta_user: {insta_user.username}]-[{type(e)}]-[err: {e}]")


@shared_task()
def comment_new_user_posts(insta_user_id):
    action = InstaAction.get_action_from_key(InstaAction.ACTION_COMMENT)
    order = dict(action=InstaAction.ACTION_COMMENT, id=0)
    insta_user = InstaUser.objects.get(user_id=insta_user_id)
    insta_user_posts = get_instagram_profile_posts(insta_user)

    action_users = InstaUser.objects.new().exclude(blocked_data__has_key=InstaAction.ACTION_COMMENT).order_by('?')[
                   :MAX_ACTION_EACH_TURN]
    for action_user in action_users:
        # random_posts = [i["id"] for i in random.choices(insta_user_posts, k=min(1, len(insta_user_posts)//3))]
        random_posts = insta_user_posts
        for data in random_posts:
            comment = Sentence.objects.order_by('?')[0]
            order['comments'] = [comment]
            order['entity_id'] = data['node']['id']
            logger.debug(
                f"[Simulator comment_new_user_posts]-[insta_user: {insta_user.username}]-[action_user: {action_user.username}]-[order: {order['entity_id']}]-[comment: {comment}]")
            try:
                do_instagram_action(action_user, order)
            except Exception as e:
                logger.warning(
                    f"[Simulator comment_new_user_posts]-[insta_user: {insta_user.username}]-[action_user: {action_user.username}]-[comment: {comment}]-[{type(e)}]-[err: {e}]")
                break
            time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{action}"])


@shared_task()
def like_new_user_posts(insta_user_id):
    action = InstaAction.get_action_from_key(InstaAction.ACTION_LIKE)
    order = dict(action=InstaAction.ACTION_LIKE, id=0)
    insta_user = InstaUser.objects.get(user_id=insta_user_id)
    insta_user_posts = get_instagram_profile_posts(insta_user)

    action_users = InstaUser.objects.new().exclude(blocked_data__has_key=InstaAction.ACTION_LIKE).order_by('?')[
                   :MAX_ACTION_EACH_TURN]
    for action_user in action_users:
        # random_posts = [i["id"] for i in random.choices(insta_user_posts, k=min(1, len(insta_user_posts)//3))]
        random_posts = insta_user_posts
        for data in random_posts:
            order['entity_id'] = data['node']['id']
            logger.debug(
                f"[Simulator like_new_user_posts]-[insta_user: {insta_user.username}]-[action_user: {action_user.username}]-[order: {order['entity_id']}]")
            try:
                do_instagram_action(action_user, order)
            except Exception as e:
                logger.warning(
                    f"[Simulator like_new_user_posts]-[insta_user: {insta_user.username}]-[action_user: {action_user.username}]-[{type(e)}]-[err: {e}]")
                break
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
            logger.warning(
                f"[Simulator follow_suggested]-[insta_user: {insta_user.username}]-[suggested: {order['entity_id']}]-[{type(e)}]-[err: {e}]")
            break
        time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{action}"])


@shared_task()
def follow_new_user(insta_user_id):
    action = InstaAction.get_action_from_key(InstaAction.ACTION_FOLLOW)
    order = dict(action=InstaAction.ACTION_FOLLOW, entity_id=insta_user_id, id=0)

    action_users = InstaUser.objects.live().exclude(blocked_data__has_key=InstaAction.ACTION_FOLLOW).order_by('?')[
                   :MAX_ACTION_EACH_TURN]
    for action_user in action_users:
        try:
            do_instagram_action(action_user, order)
        except Exception as e:
            logger.warning(
                f'[Simulator follow_new_user]-[insta_user: {insta_user_id}]-[action_user: {action_user.username}]-[{type(e)}]-[err: {e}]')
            continue
        time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{action}"])


@shared_task()
def follow_active_users(insta_user_id):
    action = InstaAction.get_action_from_key(InstaAction.ACTION_FOLLOW)
    order = dict(action=InstaAction.ACTION_FOLLOW, id=0)
    insta_user = InstaUser.objects.get(user_id=insta_user_id)
    if insta_user.is_blocked(InstaAction.ACTION_FOLLOW):
        return

    action_users = InstaUser.objects.live().order_by('?')[:MAX_ACTION_EACH_TURN]
    for action_user in action_users:
        order['entity_id'] = action_user.user_id
        try:
            do_instagram_action(insta_user, order)
        except Exception as e:
            logger.warning(
                f'[Simulator follow_active_users]-[insta_user: {insta_user.username}]-[action_user: {action_user.username}]-[{type(e)}]-[err: {e}]')
            break
        time.sleep(settings.INSTA_FOLLOW_SETTINGS[f"delay_{action}"])


@periodic_task(run_every=crontab(minute='*/1'))
def random_new_task():
    new_insta_user_ids = InstaUser.objects.new().values_list('user_id', flat=True).order_by('?')[:1]
    for insta_user_id in new_insta_user_ids:
        action_to_call = globals()[random.choice(
            random.choices((
                'follow_suggested',
                'follow_new_user',
                'follow_active_users',
                'like_new_user_posts',
                'comment_new_user_posts',
            ), weights=(10, 5, 4, 5, 1), k=25)
        )]
        action_to_call.apply_async(args=(insta_user_id,), countdown=3)


@periodic_task(run_every=crontab(minute='*/1'))
def random_manage_task():
    manageable_insta_user_ids = InstaUser.objects.manageable().values_list('user_id', flat=True).order_by('?')[:1]
    for insta_user_id in manageable_insta_user_ids:
        action_to_call = globals()[random.choice(
            random.choices((
                'change_profile_picture',
                'upload_new_user_post',
                'upload_new_user_story',
            ), weights=(10, 7, 3), k=20)
        )]
        action_to_call.apply_async(args=(insta_user_id,), countdown=3)
