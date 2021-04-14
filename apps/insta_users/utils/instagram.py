import logging
import requests
import random
from json.decoder import JSONDecodeError

from datetime import datetime

# from fake_useragent import UserAgent

from apps.insta_users.models import InstaAction

logger = logging.getLogger(__name__)

INSTAGRAM_BASE_URL = 'https://www.instagram.com'
INSTAGRAM_LOGIN_URL = f'{INSTAGRAM_BASE_URL}/accounts/login/ajax/'

# ua = UserAgent()


class InstagramMediaClosed(Exception):
    pass


def instagram_login(insta_user, commit=True):
    session = requests.Session()

    # user_agent = ua.random
    user_agent = "Instagram 10.15.0 Android (28/9; 411dpi; 1080x2220; samsung; SM-A650G; SM-A650G; Snapdragon 450; en_US)"
    session.headers = {
        'Referer': INSTAGRAM_BASE_URL,
        'user-agent': user_agent,
    }

    resp = session.get(INSTAGRAM_BASE_URL)
    session.headers.update({'X-CSRFToken': resp.cookies['csrftoken']})
    insta_user.set_proxy(session)

    login_data = {'username': insta_user.username, 'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{datetime.now().timestamp()}:{insta_user.password}'}
    login_resp = session.post(INSTAGRAM_LOGIN_URL, data=login_data, allow_redirects=True)
    session.headers.update({'X-CSRFToken': resp.cookies['csrftoken']})

    try:
        res = login_resp.json()
        status = res.get('status', '')
        is_auth = res.get('authenticated', False)
        message = res.get('message', '')

        if status == 'fail':
            logger.warning(f"[Instagram Login]-[failed for {insta_user.username}]-[res: {res}]")
            insta_user.status = insta_user.STATUS_LOGIN_LIMIT
            if message == 'checkpoint_required':
                insta_user.status = insta_user.STATUS_DISABLED
        elif is_auth:
            insta_user.status = insta_user.STATUS_ACTIVE
            # session.cookies.set('user-agent', user_agent.replace(';', '-'))
            insta_user.set_session(session.cookies.get_dict())
            insta_user.user_id = session.cookies['ds_user_id']
            logger.info(f"[Instagram Login]-[Succeeded for {insta_user.username}]")
        else:
            insta_user.status = insta_user.STATUS_LOGIN_FAILED
            logger.warning(f"[Instagram Login]-[failed for {insta_user.username}]-[res: {res}]")

    except Exception as e:
        logger.warning(f'[Instagram Login]-[insta_user: {insta_user.username}]-[{type(e)}]-[err: {e}]-[result: {login_resp.text}]')
        insta_user.status = insta_user.STATUS_DISABLED

    if commit:
        insta_user.save()


def get_instagram_session(insta_user):
    session = requests.session()
    user_session = insta_user.get_session
    # user_agent = user_session.pop('user-agent', '')
    # if user_agent:
    #     session.headers.update({
    #         'user-agent': user_agent,
    #     })
    session.headers.update({
        'X-CSRFToken': user_session['csrftoken'],
        'X-Instagram-AJAX': '7e64493c83ae',
    })
    session.cookies.update(user_session)
    insta_user.set_proxy(session)

    return session


def get_instagram_entity_data(session, order):
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
        logger.debug(f"[instagram entity check]-[HTTPError]-[action: {order['action']}]-[order: {order['id']}]-[status code: {e.response.status_code}]")
        if e.response.status_code == 404:
            raise InstagramMediaClosed('Not Found')

    except JSONDecodeError:
        logger.error(f"[instagram entity check]-[JSONDecodeError]-[action: {order['action']}]-[order: {order['id']}]-[url: {media_link}]")

    except KeyError:
        logger.error(f"[instagram entity check]-[KeyError]-[action: {order['action']}]-[order: {order['id']}]-[res: {res}]")


def instagram_like(insta_user, order):
    session = get_instagram_session(insta_user)
    get_instagram_entity_data(session, order)
    return session.post(f"https://www.instagram.com/web/likes/{order['entity_id']}/like/")


def instagram_follow(insta_user, order):
    session = get_instagram_session(insta_user)
    get_instagram_entity_data(session, order)
    return session.post(f"https://www.instagram.com/web/friendships/{order['entity_id']}/follow/")


def instagram_comment(insta_user, order):
    session = get_instagram_session(insta_user)
    get_instagram_entity_data(session, order)
    data = {
        "comment_text": random.choice(order['comments']),
        "replied_to_comment_id": ""
    }
    return session.post(f"https://www.instagram.com/web/comments/{order['entity_id']}/add/", data=data)


def do_instagram_action(insta_user, order):
    logger.debug(f"[instagram]-[insta_user: {insta_user.username}]-[action: {order['action']}]-[order: {order['id']}]")

    try:
        action = InstaAction.get_action_from_key(order['action'])
        action_to_call = globals()[f'instagram_{action}']
        _s = action_to_call(insta_user, order)
        _s.raise_for_status()

    except requests.exceptions.HTTPError as e:
        try:
            result = _s.json()
        except:
            result = {}

        logger.warning(f"[instagram]-[HTTPError]-[insta_user: {insta_user.username}]-[action: {order['action']}]-[order: {order['id']}]-[status code: {e.response.status_code}]-[body: {result}]")

        if _s.status_code == 429:
            insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_TEMP)
            insta_user.save()

        elif _s.status_code == 400:
            message = result.get('message', '')

            if message == 'feedback_required' and result.get('spam', False):
                insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_SPAM)
                # if order['action'] == InstaAction.ACTION_FOLLOW:
                #     insta_user.clear_session()

            if message == 'checkpoint_required' and not result.get('lock', True):
                insta_user.status = insta_user.STATUS_DISABLED
                insta_user.clear_session()

            if order['action'] == InstaAction.ACTION_COMMENT and result.get('status', '') == 'fail':
                insta_user.set_blocked(order['action'], InstaAction.BLOCK_TYPE_SPAM)

            insta_user.save()

        raise

    except requests.exceptions.ConnectionError:
        proxy = insta_user.proxy
        proxy.is_enable = False
        proxy.save()
        raise

    except InstagramMediaClosed as e:
        logger.warning(f"[instagram]-[Media Closed]-[action: {order['action']}]-[order: {order['link']}]-[err: {e}]")
        raise

    except Exception as e:
        logger.error(f"[instagram]-[{type(e)}]-[insta_user: {insta_user.username}]-[err: {e}]")
        raise
