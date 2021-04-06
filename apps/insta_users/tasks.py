import logging
import requests

from datetime import datetime
from django.conf import settings
from celery import shared_task

from .models import InstaUser

logger = logging.getLogger(__name__)

INSTA_FOLLOW_LOGIN_URL = f'{settings.INSTAFOLLOW_BASE_URL}/api/v1/instagram/login-verification/'

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


@shared_task
def insta_follow_login(insta_user_id):
    # getting InstaUser object
    try:
        insta_user = InstaUser.objects.get(id=insta_user_id)
    except InstaUser.DoesNotExist as e:
        logger.warning(f'[getting instafollow uuid failed]-[instauser id: {insta_user_id}]-[exc: {e}]')
        return

    # getting uuid from instafollow api
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
            f'[making request failed]-[URL: {url}]-[status code: {e.response.status_code}]'
            f'-[response err: {e.response.text}]-[exc: {e}]'
        )
        return
    except requests.exceptions.ConnectTimeout as e:
        logger.critical(f'[request failed]-[URL: {url}]-[exc: {e}]')
        return
    except Exception as e:
        logger.error(f'[request failed]-[URL: {url}]-[exc: {e}]')
        return

    return insta_user.server_key


 @shared_task
def instagram_like(pk, media_id):
    try:
        usr = InstaUser.objects.get(id=pk)
        usr_session = requests.session()
        usr_session.headers.update({'X-CSRFToken': usr.session['csrftoken']})
        usr_session.cookies.update(usr.session)
        usr_session.post(f"https://www.instagram.com/web/likes/{media_id}/like/")
        logger.info(f"post liked succeeded with the media_id of: [{media_id} and username of {usr.username}]")
    except Exception as e:
        logger.error(f"post liked succeeded with the media_id of: [{media_id} and username of {usr.username}] -- error: [{str(e)}")


@shared_task
def instagram_follow(pk, target_user):
    try:
        usr = InstaUser.objects.get(id=pk)
        usr_session = requests.session()
        usr_session.headers.update({'X-CSRFToken': usr.session['csrftoken']})
        usr_session.cookies.update(usr.session)
        usr_session.post(f"https://www.instagram.com/web/friendships/{target_user}/follow/")
        logger.info(f"follow succeeded with the target_user of: [{target_user}]")
    except Exception as e:
        logger.error(f"follow failed with the target_user of: [{target_user}] -- error: [{str(e)}")

