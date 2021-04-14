import logging
import requests
import random
from json.decoder import JSONDecodeError

from datetime import datetime

from fake_useragent import UserAgent

from apps.insta_users.models import InstaAction
from apps.proxies.models import Proxy

logger = logging.getLogger(__name__)

INSTAGRAM_BASE_URL = 'https://www.instagram.com'
INSTAGRAM_LOGIN_URL = f'{INSTAGRAM_BASE_URL}/accounts/login/ajax/'
# INSTAGRAM_LOGIN_URL = f'{INSTAGRAM_BASE_URL}/accounts/login/ajax/'
# DEVICE_SETTINGS = {
#     'manufacturer': 'Xiaomi',
#     'model': 'HM 1SW',
#     'android_version': 18,
#     'android_release': '4.3'
# }
# USER_AGENT = f'Instagram 10.26.0 Android ({android_version}/{android_release}; 320dpi; 720x1280; {manufacturer}; {model}; armani; qcom; en_US)'
# INSTAGRAM_USER_AGENT = "Instagram 10.15.0 Android (28/9; 411dpi; 1080x2220; samsung; SM-A650G; SM-A650G; Snapdragon 450; en_US)"

ua = UserAgent()


class InstagramMediaClosed(Exception):
    pass


def instagram_login(insta_user, commit=True):
    session = requests.Session()

    # user_agent = INSTAGRAM_USER_AGENT
    user_agent = ua.random
    session.headers = {
        'referer': INSTAGRAM_BASE_URL,
        'user-agent': user_agent,
        # 'content-type': 'application/x-www-form-urlencode',
        # 'referer': 'https://www.instagram.com/accounts/login/',
    }

    resp = session.get(INSTAGRAM_BASE_URL)
    session.headers.update({'X-CSRFToken': resp.cookies['csrftoken']})
    insta_user.set_proxy(session)

    login_data = {'username': insta_user.username, 'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{datetime.now().timestamp()}:{insta_user.password}'}
    login_resp = session.post(f"{INSTAGRAM_BASE_URL}/accounts/login/ajax/", data=login_data, allow_redirects=True)
    session.headers.update({'X-CSRFToken': login_resp.cookies['csrftoken']})

    try:
        try:
            result = login_resp.json()
        except:
            result = {}
        login_resp.raise_for_status()
        status = result.get('status', '')
        is_auth = result.get('authenticated', False)
        message = result.get('message', '')

        if status == 'fail':
            logger.warning(f"[Instagram Login]-[failed for {insta_user.username}]-[res: {result}]")
            insta_user.status = insta_user.STATUS_LOGIN_LIMIT
            if message == 'checkpoint_required':
                insta_user.status = insta_user.STATUS_DISABLED
        elif is_auth:
            # insta_user.status = insta_user.STATUS_ACTIVE
            session.cookies.set('user-agent', user_agent.replace(';', '-'))
            insta_user.set_session(session.cookies.get_dict())
            insta_user.user_id = session.cookies['ds_user_id']
            logger.info(f"[Instagram Login]-[Succeeded for {insta_user.username}]")
        else:
            insta_user.status = insta_user.STATUS_LOGIN_FAILED
            logger.warning(f"[Instagram Login]-[failed for {insta_user.username}]-[res: {result}]")

    except requests.exceptions.HTTPError as e:
        logger.warning(f"[Instagram Login]-[HTTPError]-[Insta_user: {insta_user.username}]-[status code: {e.response.status_code}]-[body: {result}]")
        insta_user.status = insta_user.STATUS_LOGIN_FAILED

    except Exception as e:
        logger.warning(f'[Instagram Login]-[Insta_user: {insta_user.username}]-[{type(e)}]-[err: {e}]-[result: {login_resp.text}]')
        insta_user.status = insta_user.STATUS_DISABLED

    if commit:
        insta_user.save()


def get_instagram_session(insta_user):
    session = requests.session()
    user_session = insta_user.get_session
    user_agent = user_session.pop('user-agent', '')
    if user_agent:
        session.headers.update({
            'user-agent': user_agent,
        })
    session.headers.update({
        'X-CSRFToken': user_session['csrftoken'],
        'X-Instagram-AJAX': '7e64493c83ae',
    })
    session.cookies.update(user_session)
    insta_user.set_proxy(session)

    return session


def check_instagram_entity(session, order):
    try:
        media_link = f"{order['link']}?__a=1"
        _s = session.get(media_link)
        _s.raise_for_status()
        res = _s.json()

        if order['action'] == InstaAction.ACTION_FOLLOW:
            if res['graphql']['user'].get('is_private', False):
                raise InstagramMediaClosed('Is Private')

        if order['action'] == InstaAction.ACTION_COMMENT:
            if res['graphql']['shortcode_media']['comments_disabled']:
                raise InstagramMediaClosed('Comment Closed')

            # commenting on this entity is disabled for this user
            # if res['graphql']['shortcode_media']['commenting_disabled_for_viewer']:
            #     pass

    except requests.exceptions.HTTPError as e:
        logger.debug(f"[Instagram entity check]-[HTTPError]-[action: {order['action']}]-[order: {order['id']}]-[status code: {e.response.status_code}]")
        if e.response.status_code == 404:
            raise InstagramMediaClosed('Not Found')
        if e.response.status_code == 429:
            raise

    except JSONDecodeError:
        logger.error(f"[Instagram entity check]-[JSONDecodeError]-[action: {order['action']}]-[order: {order['id']}]-[url: {media_link}]")

    except KeyError as e:
        logger.error(f"[Instagram entity check]-[KeyError]-[action: {order['action']}]-[order: {order['id']}]-[err: {e}]")


def get_instagram_suggested_follows(insta_user):
    session = get_instagram_session(insta_user)

    params = dict(
        query_hash='ed2e3ff5ae8b96717476b62ef06ed8cc',
        variables='{"fetch_suggested_count": 30, "include_media": false}'
    )
    try:
        resp = session.get(f"{INSTAGRAM_BASE_URL}/graphql/query/", params=params)
        result = resp.json()['data']['user']['edge_suggested_users']['edges']
    except:
        result = []

    return result


def do_instagram_like(session, entity_id):
    return session.post(f"{INSTAGRAM_BASE_URL}/web/likes/{entity_id}/like/")


def do_instagram_follow(session, entity_id):
    return session.post(f"{INSTAGRAM_BASE_URL}/web/friendships/{entity_id}/follow/")


def do_instagram_comment(session, entity_id, comment):
    data = {
        "comment_text": comment,
        "replied_to_comment_id": ""
    }
    return session.post(f"{INSTAGRAM_BASE_URL}/web/comments/{entity_id}/add/", data=data)


def do_instagram_action(insta_user, order):
    logger.debug(f"[Instagram]-[Insta_user: {insta_user.username}]-[action: {order['action']}]-[order: {order['id']}]")

    try:
        session = get_instagram_session(insta_user)
        check_instagram_entity(session, order)
        action = InstaAction.get_action_from_key(order['action'])
        action_to_call = globals()[f'do_instagram_{action}']
        args = (session, order['entity_id'])
        if order['action'] == InstaAction.ACTION_COMMENT:
            args += (random.choice(order['comments']), )
        _s = action_to_call(*args)
        _s.raise_for_status()

    except requests.exceptions.HTTPError as e:

        status_code = e.response.status_code

        try:
            result = e.response.json()
        except:
            result = {}

        logger.warning(f"[Instagram do action]-[HTTPError]-[Insta_user: {insta_user.username}]-[action: {order['action']}]-[order: {order['id']}]-[status code: {status_code}]-[body: {result}]")

        if status_code == 429:
            insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_TEMP)
            insta_user.proxy_id = Proxy.get_proxy()
            insta_user.save()

        elif status_code == 400:
            message = result.get('message', '')
            status = result.get('status', '')

            if message == 'feedback_required' and result.get('spam', False):
                insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_SPAM)
                # if order['action'] == InstaAction.ACTION_FOLLOW:
                #     insta_user.clear_session()

            if message == 'checkpoint_required' and not result.get('lock', True):
                insta_user.status = insta_user.STATUS_DISABLED
                insta_user.clear_session()

            if order['action'] == InstaAction.ACTION_FOLLOW and status == 'fail' and "following the max limit of accounts" in message:
                insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_PERM)

            if order['action'] == InstaAction.ACTION_COMMENT and status == 'fail':
                insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_SPAM)

            insta_user.save()

        raise

    except requests.exceptions.ConnectionError:
        proxy = insta_user.proxy
        proxy.is_enable = False
        proxy.save()
        raise

    except InstagramMediaClosed as e:
        logger.warning(f"[Instagram do action]-[Media Closed]-[action: {order['action']}]-[order: {order['link']}]-[err: {e}]")
        raise

    except Exception as e:
        logger.error(f"[Instagram do action]-[{type(e)}]-[Insta_user: {insta_user.username}]-[err: {e}]")
        raise
