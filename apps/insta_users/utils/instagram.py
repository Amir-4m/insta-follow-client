import logging
import requests

from datetime import datetime
# from apps.insta_users.models import InstaAction

logger = logging.getLogger(__name__)

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
    insta_user.set_proxy(session)

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


def get_action_session(insta_user):
    session = requests.session()
    session.headers.update({'X-CSRFToken': insta_user.session['csrftoken']})
    session.headers.update({'X-Instagram-AJAX': '7e64493c83ae'})
    session.cookies.update(insta_user.session)
    insta_user.set_proxy(session)

    return session


def do_instagram_action(insta_user, order):

    logger.debug(f"[instagram]-[insta_user: {insta_user.username}]-[action: {order['action']}]-[target: {order['entity_id']}]")

    try:
        _s = instagram_follow(insta_user, order['entity_id'])
        _s.raise_for_status()

    except requests.exceptions.HTTPError as e:
        logger.warning(f'[instagram]-[HTTPError]-[insta_user: {insta_user.username}]-[status code: {e.response.status_code}]-[err: {e.response.text}]')

        if _s.status_code == 429:
            insta_user.status = insta_user.STATUS_BLOCKED_TEMP
            insta_user.save()

        elif _s.status_code == 400:
            is_spam = _s.json().get('spam', False)
            if is_spam:
                insta_user.status = insta_user.STATUS_BLOCKED
                insta_user.save()
        raise

    except Exception as e:
        logger.error(f'[instagram]-[{type(e)}]-[insta_user: {insta_user.username}]-[err: {e}]')
        raise


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

