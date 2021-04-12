import logging
import requests
import random

from datetime import datetime

from fake_useragent import UserAgent

from apps.proxies.models import Proxy
from apps.insta_users.models import InstaAction

logger = logging.getLogger(__name__)

INSTAGRAM_BASE_URL = 'https://www.instagram.com'
INSTAGRAM_LOGIN_URL = f'{INSTAGRAM_BASE_URL}/accounts/login/ajax/'

ua = UserAgent()


def instagram_login(insta_user, commit=True):
    session = requests.Session()

    session.headers = {
        'Referer': INSTAGRAM_BASE_URL,
        'user-agent': ua.random,
    }

    resp = session.get(INSTAGRAM_BASE_URL)
    session.headers.update({'X-CSRFToken': resp.cookies['csrftoken']})
    insta_user.proxy_id = Proxy.get_proxy()
    insta_user.set_proxy(session)

    login_data = {'username': insta_user.username, 'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{datetime.now().timestamp()}:{insta_user.password}'}
    login_resp = session.post(INSTAGRAM_LOGIN_URL, data=login_data, allow_redirects=True)
    session.headers.update({'X-CSRFToken': resp.cookies['csrftoken']})

    try:
        is_auth = login_resp.json()['authenticated']
        if is_auth:
            insta_user.status = insta_user.STATUS_ACTIVE
            insta_user.session = session.cookies.get_dict()
            insta_user.user_id = session.cookies['ds_user_id']
            logger.info(f"[Instagram Login]-[Succeeded for {insta_user.username}]")
        else:
            insta_user.status = insta_user.STATUS_LOGIN_FAILED

    except KeyError:
        logger.warning(f'[Instagram Login]-[insta_user: {insta_user.username}]-[result: {login_resp.json()}]')
        insta_user.status = insta_user.STATUS_DISABLED

    except Exception as e:
        logger.warning(f'[Instagram Login]-[insta_user: {insta_user.username}]-[{type(e)}]-[err: {e}]-[result: {login_resp.text}]')
        insta_user.status = insta_user.STATUS_LOGIN_FAILED

    if commit:
        insta_user.save()


def get_action_session(insta_user):
    session = requests.session()
    session.headers.update({'X-CSRFToken': insta_user.session['csrftoken']})
    session.headers.update({'X-Instagram-AJAX': '7e64493c83ae'})
    session.cookies.update(insta_user.session)
    insta_user.set_proxy(session)

    return session


def instagram_like(insta_user, media_id):
    session = get_action_session(insta_user)
    return session.post(f"https://www.instagram.com/web/likes/{media_id}/like/")


def instagram_follow(insta_user, target_user):
    session = get_action_session(insta_user)
    return session.post(f"https://www.instagram.com/web/friendships/{target_user}/follow/")


def instagram_comment(insta_user, media_id, comment):
    session = get_action_session(insta_user)
    data = {
        "comment_text": comment,
        "replied_to_comment_id": ""
    }
    return session.post(f"https://www.instagram.com/web/comments/{media_id}/add/", data=data)


def do_instagram_action(insta_user, order):

    logger.debug(f"[instagram]-[insta_user: {insta_user.username}]-[action: {order['action']}]-[target: {order['entity_id']}]")

    try:
        action = InstaAction.get_action_from_key(order['action'])
        action_to_call = globals()[f'instagram_{action}']
        args = (insta_user, order['entity_id'])
        if order['action'] == InstaAction.ACTION_COMMENT:
            args += (random.choice(order['comments']),)

        _s = action_to_call(*args)
        _s.raise_for_status()

    except requests.exceptions.HTTPError as e:
        log_txt = f'[instagram]-[HTTPError]-[insta_user: {insta_user.username}]-[status code: {e.response.status_code}]'
        if 'json' in _s.headers['content-type']:
            log_txt += f'-[err: {e.response.text}]'
        logger.warning(log_txt)

        if _s.status_code == 429:
            insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_TEMP)
            insta_user.save()

        elif _s.status_code == 400:
            result = _s.json()
            message = result.get('message', '')

            if message == 'feedback_required' and result.get('spam', False):
                insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_SPAM)
                # if order['action'] == InstaAction.ACTION_FOLLOW:
                #     insta_user.clear_session()

            if message == 'checkpoint_required' and not result.get('lock', True):
                insta_user.status = insta_user.STATUS_DISABLED
                insta_user.clear_session()

            if order['action'] == InstaAction.ACTION_COMMENT and result.get('status', '') == 'fail':
                return False

            insta_user.save()

        raise

    except Exception as e:
        logger.error(f'[instagram]-[{type(e)}]-[insta_user: {insta_user.username}]-[err: {e}]')
        raise

    return True
