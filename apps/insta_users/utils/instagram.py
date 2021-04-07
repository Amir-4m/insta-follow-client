import logging
import requests

from datetime import datetime

logger = logging.getLogger(__file__)

INSTAGRAM_BASE_URL = 'https://www.instagram.com'
INSTAGRAM_LOGIN_URL = f'{INSTAGRAM_BASE_URL}/accounts/login/ajax/'


def instagram_login(insta_user, commit=True):
    session = requests.Session()
    session.headers = {
        'Referer': INSTAGRAM_BASE_URL,
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; ) Gecko/20100101 Firefox/65.0",
    }

    resp = session.get(INSTAGRAM_BASE_URL)
    session.headers.update({'X-CSRFToken': resp.cookies['csrftoken']})
    login_data = {'username': insta_user.username, 'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{datetime.now().timestamp()}:{insta_user.password}'}

    login_resp = session.post(INSTAGRAM_LOGIN_URL, data=login_data, allow_redirects=True)
    session.headers.update({'X-CSRFToken': resp.cookies['csrftoken']})

    try:
        is_auth = login_resp.json()['authenticated']
    except Exception as e:
        is_auth = False
        logger.critical(f'[Instagram Login]-[{type(e)}]-[err: {e}]')

    if is_auth:
        insta_user.session = session.cookies.get_dict()
        insta_user.user_id = session.cookies['ds_user_id']
        logger.info(f"[Instagram Login]-[Succeeded for {insta_user.username}]")
    else:
        insta_user.username = None
        insta_user.status = insta_user.STATUS_WRONG

    if commit:
        insta_user.save()


def instagram_like(insta_user, media_id):
    session = requests.session()
    session.headers.update({'X-CSRFToken': insta_user.session['csrftoken']})
    session.cookies.update(insta_user.session)

    session.post(f"https://www.instagram.com/web/likes/{media_id}/like/")
    logger.debug(f"[like succeeded]-[insta_user: {insta_user.username}]-[media_id: {media_id}]")


def instagram_follow(insta_user, target_user):
    session = requests.session()
    session.headers.update({'X-CSRFToken': insta_user.session['csrftoken']})
    session.cookies.update(insta_user.session)

    session.post(f"https://www.instagram.com/web/friendships/{target_user}/follow/")
    logger.debug(f"[follow succeeded]-[insta_user: {insta_user.username}]-[target_user: {target_user}]")


def instagram_comment(insta_user, media_id, comment):
    session = requests.session()
    session.headers.update({'X-CSRFToken': insta_user.session['csrftoken']})
    session.cookies.update(insta_user.session)
    data = {
        "comment_text": comment,
        "replied_to_comment_id": ""
    }

    session.post(f"https://www.instagram.com/web/comments/{media_id}/add/", data=data)
    logger.debug(f"[comment succeeded]-[insta_user: {insta_user.username}]-[media_id: {media_id}]")
