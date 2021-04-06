import logging
import os

import requests

from datetime import datetime

from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings
from celery import shared_task
from pid import PidFile

from .models import InstaUser
from .utils import get_insta_follow_token

logger = logging.getLogger(__name__)

INSTA_FOLLOW_LOGIN_URL = f'{settings.INSTAFOLLOW_BASE_URL}/api/v1/instagram/login-verification/'
INSTA_FOLLOW_ORDERS_URL = f'{settings.INSTAFOLLOW_BASE_URL}/api/v1/instagram/orders/'

INSTAGRAM_BASE_URL = 'https://www.instagram.com'
INSTAGRAM_LOGIN_URL = f'{INSTAGRAM_BASE_URL}/accounts/login/ajax/'

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


def stop_duplicate_task(func):
    def inner_function():
        file_lock = check_running(func.__name__)
        if not file_lock:
            logger.error(f"[Another {func.__name__} is already running]")
            return False
        func()
        if file_lock:
            file_lock.close()
        return True

    return inner_function


def check_running(function_name):
    if not os.path.exists('/tmp'):
        os.mkdir('/tmp')
    file_lock = PidFile(str(function_name), piddir='/tmp')
    try:
        file_lock.create()
        return file_lock
    except:
        return None


@shared_task
def instagram_login(insta_user_id):
    try:
        insta_user = InstaUser.objects.get(id=insta_user_id, session='')
    except InstaUser.DoesNotExist as e:
        logger.warning(f'[getting instafollow uuid failed]-[instauser id: {insta_user_id}]-[exc: {e}]')
        return

    session = requests.Session()
    session.headers = {
        'Referer': INSTAGRAM_BASE_URL,
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; ) Gecko/20100101 Firefox/65.0",
    }

    resp = session.get(INSTAGRAM_BASE_URL)
    session.headers.update({'X-CSRFToken': resp.cookies['csrftoken']})
    login_data = {'username': insta_user.username, 'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{datetime.now().timestamp()}:{insta_user.password}'}

    try:
        login_resp = session.post(INSTAGRAM_LOGIN_URL, data=login_data, allow_redirects=True)
        session.headers.update({'X-CSRFToken': resp.cookies['csrftoken']})
        if login_resp.json()['authenticated']:
            insta_user.session = session.cookies.get_dict()
            insta_user.user_id = session.cookies['ds_user_id']
            insta_user.save()
            logger.info(f"log in succeeded for {insta_user.username}")
    except Exception as e:
        logger.error(f"log in failed for {insta_user.username} - [error: {e}]")


def instagram_like(insta_user, media_id):
    session = requests.session()
    session.headers.update({'X-CSRFToken': insta_user.session['csrftoken']})
    session.cookies.update(insta_user.session)

    try:
        session.post(f"https://www.instagram.com/web/likes/{media_id}/like/")
        logger.info(f"[like succeeded] - [media_id: {media_id}] - [insta_user: {insta_user.username}]")
    except Exception as e:
        logger.info(f"[like failed] - [media_id: {media_id}] - [insta_user: {insta_user.username}] - [error: {e}]")


def instagram_follow(insta_user, target_user):
    session = requests.session()
    session.headers.update({'X-CSRFToken': insta_user.session['csrftoken']})
    session.cookies.update(insta_user.session)

    try:
        session.post(f"https://www.instagram.com/web/friendships/{target_user}/follow/")
        logger.info(f"[follow succeeded] - [target_user: {target_user}] - [insta_user: {insta_user.username}]")
    except Exception as e:
        logger.info(f"[follow failed] - [target_user: {target_user}] - [insta_user: {insta_user.username}] - [error: {e}]")

@shared_task
def instagram_comment(insta_user, media_id, comment):
    session = requests.session()
    session.headers.update({'X-CSRFToken': insta_user.session['csrftoken']})
    session.cookies.update(insta_user.session)
    data = {
        "comment_text": comment,
        "replied_to_comment_id": ""
    }

    try:
        session.post(f"https://www.instagram.com/web/comments/{media_id}/add/", data=data)
        logger.info(f"[comment succeeded] - [media_id: {media_id}] - [insta_user: {insta_user.username}]")
    except Exception as e:
        logger.info(f"[comment failed] - [target_user: {media_id}] - [insta_user: {insta_user.username}] - [error: {e}]")


@shared_task
def insta_follow_login(insta_user_id):
    # getting InstaUser object
    try:
        insta_user = InstaUser.objects.get(id=insta_user_id)
    except InstaUser.DoesNotExist as e:
        logger.warning(f'[getting instafollow uuid failed]-[instauser id: {insta_user_id}]-[exc: {e}]')
        return

    # getting uuid from insta_follow api
    parameter = dict(
        instagram_user_id=insta_user.user_id,
        instagram_username=insta_user.username,
        session_id=insta_user.session
    )
    url = INSTA_FOLLOW_LOGIN_URL
    logger.debug(f"[calling api]-[URL: {url}]-[data: {parameter}]")

    try:
        response = requests.post(url, json=parameter)
        insta_user.server_key = response.json().get('uuid')
        insta_user.save()
    except requests.exceptions.HTTPError as e:
        logger.warning(
            f'[HTTPError]-[URL: {url}]-[status code: {e.response.status_code}]'
            f'-[response err: {e.response.text}]-[error: {e}]'
        )
        return
    except requests.exceptions.ConnectTimeout as e:
        logger.critical(f'[ConnectTimeout]-[URL: {url}]-[error: {e}]')
        return
    except Exception as e:
        logger.error(f'[{type(e)}]-[URL: {url}]-[error: {e}]')
        return

    return insta_user.server_key


def get_insta_follow_order_by_action(insta_user, action):
    # TODO needs to fill this field `server_key` here ??
    if not insta_user.server_key:
        logger.warning(f'[insta user has no server key]-[insta user id: {insta_user.id}]')
        return

    params = dict(
        page_size=5,
        action=action
    )
    url = INSTA_FOLLOW_ORDERS_URL

    logger.debug(
        f"[getting instafollow orders]-[URL: {url}]-[insta user id: {insta_user.id}]-[params: {params}]"
    )

    # getting orders from api
    try:
        headers = dict(Authorization=get_insta_follow_token(insta_user.server_key))
        response = requests.get(url, params=params, headers=headers)
        res = response.json()

    except requests.exceptions.HTTPError as e:
        logger.warning(
            f'[HTTPError]-[URL: {url}]-[status code: {e.response.status_code}]'
            f'-[response err: {e.response.text}]-[error: {e}]'
        )
        return
    except requests.exceptions.ConnectTimeout as e:
        logger.critical(f'[ConnectTimeout]-[URL: {url}]-[error: {e}]')
        return
    except Exception as e:
        logger.error(f'[{type(e)}]-[URL: {url}]-[error: {e}]')
        return

    return res


@periodic_task(run_every=crontab(minute='*'))
def p_insta_user_action():
    insta_user_action()


@stop_duplicate_task
def insta_user_action():
    all_insta_users = InstaUser.objects.live()
    for usr in all_insta_users:
        instagram_follow.apply_async(
            args=(usr, "target_user")
        )
