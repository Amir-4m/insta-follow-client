import logging

from .models import InstaUser
from django.conf import settings
import requests

logger = logging.getLogger(__file__)

JSON_HEADERS = {'Content-type': 'application/json'}

INSTAFOLLOW_BASE_URL = settings.INSTAFOLLOW_BASE_URL
LOGIN_VERIFICATION_URL = f'{INSTAFOLLOW_BASE_URL}/api/v1/instagram/login-verification/'


def custom_request(url, method='post', **kwargs):
    try:
        logger.debug(f"[making request]-[method: {method}]-[URL: {url}]-[kwargs: {kwargs}]")
        req = requests.request(method, url, **kwargs)
        req.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.warning(
            f'[making request failed]-[response err: {e.response.text}]-[status code: {e.response.status_code}]'
            f'-[URL: {url}]-[exc: {e}]'
        )
        raise Exception(e.response.text)
    except requests.exceptions.ConnectTimeout as e:
        logger.critical(f'[request failed]-[URL: {url}]-[exc: {e}]')
        raise
    except Exception as e:
        logger.error(f'[request failed]-[URL: {url}]-[exc: {e}]')
        raise
    return req


def get_instafollow_uuid(insta_user_id):
    # getting InstaUser object
    try:
        instauser = InstaUser.objects.get(id=insta_user_id)
    except InstaUser.DoesNotExist as e:
        logger.warning(f'[getting instafollow uuid failed]-[instauser id: {insta_user_id}]-[exc: {e}]')
        raise

    parameter = dict(
        instagram_user_id=instauser.user_id,
        instagram_username=instauser.username,
        session_id=instauser.session
    )

    # getting uuid from instafollow api
    response = custom_request(LOGIN_VERIFICATION_URL, json=parameter, header=JSON_HEADERS)
    instafollow_uuid = response.json().get('uuid')

    instauser.server_key = instafollow_uuid
    instauser.save()

    return instauser

