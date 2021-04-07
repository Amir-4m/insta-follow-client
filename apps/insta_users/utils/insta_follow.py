import logging
import requests

from datetime import datetime
from base64 import b64decode, b64encode

from django.conf import settings
from django.utils.encoding import smart_text

from Crypto.Cipher import AES
from Crypto import Random

logger = logging.getLogger(__file__)

INSTA_FOLLOW_LOGIN_URL = f'{settings.INSTAFOLLOW_BASE_URL}/api/v1/instagram/login-verification/'
INSTA_FOLLOW_ORDERS_URL = f'{settings.INSTAFOLLOW_BASE_URL}/api/v1/instagram/orders/'
INSTA_FOLLOW_INQUIRIES = f'{settings.INSTAFOLLOW_BASE_URL}/instagram/inquiries/done/'


class CryptoService:

    def __init__(self, key):
        """
        Requires string param as a key
        """
        self.key = key
        self.BS = AES.block_size

    def __pad(self, s):
        return s + (self.BS - len(s) % self.BS) * chr(self.BS - len(s) % self.BS)

    @staticmethod
    def __unpad(s):
        return s[0:-ord(s[-1])]

    def encrypt(self, raw):
        """
        Returns b64encode encoded encrypted value!
        """
        raw = self.__pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        """
        Requires b64encode encoded param to decrypt
        """
        enc = b64decode(enc)
        iv = enc[:16]
        enc = enc[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.__unpad(cipher.decrypt(enc).decode())


def generate_insta_follow_token(insta_user_server_key):
    dt = datetime.utcnow()
    token = CryptoService(dt.strftime("%d%m%y%H") + dt.strftime("%d%m%y%H")).encrypt(str(insta_user_server_key))
    return f'Token {smart_text(token)}'


def get_insta_follow_uuid(insta_user):
    params = dict(
        instagram_user_id=insta_user.user_id,
        instagram_username=insta_user.username,
        session_id=insta_user.session['sessionid']
    )
    url = INSTA_FOLLOW_LOGIN_URL
    logger.debug(f"[insta_follow register]-[insta user id: {insta_user.id}]-[params: {params}]")

    try:
        response = requests.post(url, json=params)
        return response.json()['uuid']
    except requests.exceptions.HTTPError as e:
        logger.warning(f'[insta_follow register]-[HTTPError]-[status code: {e.response.status_code}]-[err: {e.response.text}]')
    except requests.exceptions.ConnectTimeout as e:
        logger.critical(f'[insta_follow register]-[ConnectTimeout]-[err: {e}]')
    except Exception as e:
        logger.error(f'[insta_follow register]-[{type(e)}]-[URL: {url}]-[err: {e}]')


def insta_follow_get_orders(insta_user, action):
    params = dict(limit=settings.INSTAFOLLOW_ORDER_LIMIT)
    url = f'{INSTA_FOLLOW_ORDERS_URL}{action}/'

    logger.debug(f"[insta_follow orders]-[insta user id: {insta_user.id}]-[params: {params}]")

    res = []
    try:
        headers = dict(Authorization=generate_insta_follow_token(insta_user.server_key))
        response = requests.get(url, params=params, headers=headers)
        res = response.json()
    except requests.exceptions.HTTPError as e:
        logger.warning(f'[insta_follow orders]-[HTTPError]-[status code: {e.response.status_code}]-[err: {e.response.text}]')
    except requests.exceptions.ConnectTimeout as e:
        logger.critical(f'[insta_follow orders]-[ConnectTimeout]-[err: {e}]')
    except Exception as e:
        logger.error(f'[insta_follow orders]-[{type(e)}]-[URL: {url}]-[err: {e}]')

    return res


def insta_follow_order_done(insta_user, order_id):
    # if instagram_follow(insta_user, order['target_no']):
    url = INSTA_FOLLOW_INQUIRIES
    try:
        headers = dict(Authorization=generate_insta_follow_token(insta_user.server_key))
        requests.post(url, json={'order_id': order_id}, headers=headers)
    except requests.exceptions.HTTPError as e:
        logger.warning(f'[insta_follow order done]-[HTTPError]-[status code: {e.response.status_code}]-[err: {e.response.text}]')
    except requests.exceptions.ConnectTimeout as e:
        logger.critical(f'[insta_follow order done]-[ConnectTimeout]-[err: {e}]')
    except Exception as e:
        logger.error(f'[insta_follow order done]-[{type(e)}]-[URL: {url}]-[err: {e}]')
