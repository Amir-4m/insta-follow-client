import logging

import requests
import random
from json.decoder import JSONDecodeError

from datetime import datetime

from fake_useragent import UserAgent

from apps.insta_users.models import InstaAction
from apps.proxies.models import Proxy
from utils.images import resize_image

logger = logging.getLogger(__name__)

INSTAGRAM_BASE_URL = 'https://www.instagram.com'
INSTAGRAM_LOGIN_URL = f'{INSTAGRAM_BASE_URL}/accounts/login/ajax/'
INSTAGRAM_GRAPHQL_URL = f'{INSTAGRAM_BASE_URL}/graphql/query/'

INSTAGRAM_LEGACY_BASE_URL = 'https://i.instagram.com'

# DEVICE_SETTINGS = {
#     'manufacturer': 'Xiaomi',
#     'model': 'HM 1SW',
#     'android_version': 18,
#     'android_release': '4.3'
# }
# USER_AGENT = f'Instagram 10.26.0 Android ({android_version}/{android_release}; 320dpi; 720x1280; {manufacturer}; {model}; armani; qcom; en_US)'
# INSTAGRAM_USER_AGENT = "Instagram 10.15.0 Android (28/9; 411dpi; 1080x2220; Samsung; SM-A650G; Snapdragon 450; en_US)"
INSTAGRAM_USER_AGENT = "Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2 XL Build/OPD1.170816.004) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Mobile Safari/537.36"

ua = UserAgent()


class InstagramMediaClosed(Exception):
    pass


class InstagramActionFailed(Exception):
    pass


def instagram_login(insta_user, commit=True):
    session = requests.Session()
    insta_user.set_session_proxy(session)

    user_agent = ua.random
    # user_agent = INSTAGRAM_USER_AGENT
    session.headers = {
        'Referer': f"{INSTAGRAM_BASE_URL}/accounts/login/",
        'User-Agent': user_agent,
        "Content-Type": "application/x-www-form-urlencoded",
        # 'content-type': 'application/x-www-form-urlencode',
        # 'referer': 'https://www.instagram.com/accounts/login/',
    }

    resp = session.get(INSTAGRAM_BASE_URL)
    session.headers.update({
        "X-CSRFToken": resp.cookies['csrftoken'],
    })

    login_data = {'username': insta_user.username, 'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{datetime.now().timestamp()}:{insta_user.password}'}
    login_resp = session.post(f"{INSTAGRAM_BASE_URL}/accounts/login/ajax/", data=login_data, allow_redirects=True)

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
            # session.headers.update({'X-CSRFToken': login_resp.cookies['csrftoken']})
            insta_user.set_session(session.cookies.get_dict())
            insta_user.user_id = session.cookies['ds_user_id']
            insta_user.user_agent = user_agent
            logger.info(f"[Instagram Login]-[Succeeded for {insta_user.username}]")
        else:
            insta_user.status = insta_user.STATUS_LOGIN_FAILED
            logger.warning(f"[Instagram Login]-[failed for {insta_user.username}]-[res: {result}]")

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        logger.warning(f"[Instagram Login]-[HTTPError]-[Insta_user: {insta_user.username}]-[status code: {e.response.status_code}]-[body: {result}]")
        insta_user.status = insta_user.STATUS_LOGIN_FAILED
        if status_code == 429:
            insta_user.status = insta_user.STATUS_LOGIN_LIMIT

    except Exception as e:
        logger.warning(f'[Instagram Login]-[Insta_user: {insta_user.username}]-[{type(e)}]-[err: {e}]-[result: {login_resp.text}]')
        insta_user.status = insta_user.STATUS_DISABLED

    if commit:
        insta_user.save()


def get_instagram_session(insta_user, set_proxy=True, user_agent=''):
    session = requests.session()
    user_session = insta_user.get_session
    if not user_agent:
        user_agent = insta_user.user_agent
    if user_agent:
        session.headers.update({
            'user-agent': user_agent,
        })
    session.headers.update({
        'X-CSRFToken': user_session['csrftoken'],
        'X-Instagram-AJAX': '7e64493c83ae',
    })
    session.cookies.update(user_session)
    if set_proxy:
        insta_user.set_session_proxy(session)

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
        logger.warning(f"[Instagram entity check]-[JSONDecode]-[action: {order['action']}]-[order: {order['id']}]-[url: {media_link}]")

    except KeyError as e:
        logger.warning(f"[Instagram entity check]-[KeyError]-[action: {order['action']}]-[order: {order['id']}]-[err: {e}]")


def has_instagram_profile_picture(insta_user, session=None):
    if session is None:
        session = get_instagram_session(insta_user)

    has_picture_key = "s150x150"

    profile_link = f"{INSTAGRAM_BASE_URL}/{insta_user.username}/"
    params = dict(__a=1)
    try:
        resp = session.get(profile_link, params=params)
        profile_pic_url = resp.json()['graphql']['user']['profile_pic_url']
        result = has_picture_key in profile_pic_url
    except Exception as e:
        logger.warning(f"[Instagram check profile pic]-[{type(e)}]-[insta_user: {insta_user.username}]-[err: {e}]")
        return

    return result


def change_instagram_profile_pic(insta_user, image_field, session=None):
    if session is None:
        session = get_instagram_session(insta_user)

    files = {
        "profile_pic": open(image_field.path, 'rb')
    }
    data = {
        "Content-Disposition": "form-data",
        "Content-Type": "image/jpeg",
        "name": "profile_pic",
        "filename": image_field.name.split('/')[-1],
    }

    _s = session.post(f"{INSTAGRAM_BASE_URL}/accounts/web_change_profile_picture/", files=files, data=data)
    _s.raise_for_status()


def get_instagram_profile_posts(insta_user, session=None):
    if session is None:
        session = get_instagram_session(insta_user)

    profile_link = f"{INSTAGRAM_BASE_URL}/{insta_user.username}/"
    params = dict(__a=1)
    try:
        resp = session.get(profile_link, params=params)
        result = resp.json()['graphql']['user']['edge_owner_to_timeline_media']['edges']
    except Exception as e:
        logger.warning(f"[Instagram get posts]-[{type(e)}]-[insta_user: {insta_user.username}]-[err: {e}]")
        result = []

    return result


def get_instagram_explorer_posts(insta_user):
    session = get_instagram_session(insta_user)

    params = dict(
        query_hash='8f0a6bb6a0450ede10d2f0d46fd6c771',
        variables='{"has_threaded_comments": true}'
    )
    try:
        resp = session.get(INSTAGRAM_GRAPHQL_URL, params=params)
        result = resp.json()['data']['user']['edge_web_feed_timeline']['edges']
    except:
        result = []

    return result


def get_instagram_suggested_follows(insta_user):
    session = get_instagram_session(insta_user)

    params = dict(
        query_hash='ed2e3ff5ae8b96717476b62ef06ed8cc',
        variables='{"fetch_suggested_count": 30, "include_media": false}'
    )
    try:
        resp = session.get(INSTAGRAM_GRAPHQL_URL, params=params)
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
    logger.debug(f"[Instagram do action]-[insta_user: {insta_user.username}]-[action: {order['action']}]-[order: {order['entity_id']}]")

    try:
        session = get_instagram_session(insta_user)
        # check_instagram_entity(session, order)
        action = InstaAction.get_action_from_key(order['action'])
        action_to_call = globals()[f'do_instagram_{action}']
        args = (session, order['entity_id'])
        if order['action'] == InstaAction.ACTION_COMMENT:
            args += (random.choice(order['comments']), )
        _s = action_to_call(*args)
        status_code = _s.status_code

        try:
            result = _s.json()
        except:
            result = {}

        if status_code == requests.codes.ok and result.get('status', '') == 'ok':
            return

        logger.warning(f"[Instagram do action]-[HTTPError]-[insta_user: {insta_user.username}]-[action: {order['action']}]-"
                       f"[order: {order['entity_id']}]-[status code: {status_code}]-[header: {session.headers}]-[proxy: {session.proxies}]-[body: {result}]")

        if status_code == requests.codes.ok and 'ds_user_id' not in _s.cookies.get_dict():
            insta_user.clear_session()

        if status_code == 429:
            insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_TEMP)
            insta_user.proxy_id = Proxy.get_proxy()

        if status_code == 400:
            message = result.get('message', '')
            status = result.get('status', '')

            if message == 'feedback_required' and result.get('spam', False):
                insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_SPAM)

            if message == 'checkpoint_required' and not result.get('lock', True):
                insta_user.clear_session()

            if order['action'] == InstaAction.ACTION_FOLLOW and status == 'fail' and "following the max limit of accounts" in message:
                insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_PERM)

            if order['action'] == InstaAction.ACTION_COMMENT and status == 'fail':
                insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_SPAM)

        if status_code == 403:
            insta_user.clear_session()

        insta_user.save()
        raise InstagramActionFailed(f"{status_code} - {result}")

    # except requests.exceptions.ConnectionError:
    #     proxy = insta_user.proxy
    #     proxy.is_enable = False
    #     proxy.save()
    #     raise

    except InstagramActionFailed:
        raise

    except InstagramMediaClosed as e:
        logger.warning(f"[Instagram do action]-[MediaClosed]-[action: {order['action']}]-[order: {order['link']}]-[err: {e}]")
        raise

    except Exception as e:
        logger.error(f"[Instagram do action]-[{type(e)}]-[insta_user: {insta_user.username}]-[err: {e}]")
        raise


def upload_instagram_post(session, image_field, caption=''):
    microtime = int(datetime.now().timestamp())

    if image_field.width != image_field.height:
        im_resized, image_size, image_data = resize_image(image_field)
        image_width = im_resized.width
        image_height = im_resized.height

    else:
        image_size = image_field.size
        image_width = image_field.width
        image_height = image_field.height
        image_data = image_field.path

    headers = {
        "user-agent": INSTAGRAM_USER_AGENT,
        "content-type": "image/jpeg",
        "offset": "0",
        "x-entity-type": "image/jpeg",
        "x-entity-length": f"{image_size}",
        "x-entity-name": f"fb_uploader_{microtime}",
        "x-instagram-rupload-params": f'{{"media_type":1,"upload_id":"{microtime}","upload_media_height":{image_height},"upload_media_width":{image_width}}}',
    }
    session.headers.update(headers)

    with open(image_data, 'rb') as image_file:
        _s1 = session.post(f"{INSTAGRAM_BASE_URL}/rupload_igphoto/fb_uploader_{microtime}", data=image_file)
        _s1.raise_for_status()

    headers = {
        "user-agent": INSTAGRAM_USER_AGENT,
        "content-type": "application/x-www-form-urlencoded"
    }
    body = {
        'upload_id': microtime,
        'caption': caption,
        'source_type': 'library',
        'custom_accessibility_caption': '',
        'usertags': '',
    }
    session.headers.update(headers)
    _s2 = session.post(f"{INSTAGRAM_BASE_URL}/create/configure/", data=body)
    _s2.raise_for_status()


def upload_instagram_story(session, image_field):
    microtime = int(datetime.now().timestamp())

    headers = {
        "user-agent": INSTAGRAM_USER_AGENT,
        "content-type": "image/jpeg",
        "offset": "0",
        "x-entity-type": "image/jpeg",
        "x-entity-length": f"{image_field.size}",
        "x-entity-name": f"fb_uploader_{microtime}",
        "x-instagram-rupload-params": f'{{"media_type":1,"upload_id":"{microtime}","upload_media_height":{image_field.height},"upload_media_width":{image_field.width}}}',
    }
    session.headers.update(headers)
    _s1 = session.post(f"{INSTAGRAM_BASE_URL}/rupload_igphoto/fb_uploader_{microtime}", data=open(image_field.path, 'rb'))
    _s1.raise_for_status()

    headers = {
        "user-agent": INSTAGRAM_USER_AGENT,
        "content-type": "application/x-www-form-urlencoded"
    }
    body = {
        'upload_id': microtime,
        'source_type': 'library',
        'custom_accessibility_caption': '',
        'usertags': '',
    }
    session.headers.update(headers)
    _s2 = session.post(f"{INSTAGRAM_BASE_URL}/create/configure_to_story/", data=body)
    _s2.raise_for_status()
