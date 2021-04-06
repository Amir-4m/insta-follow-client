import logging

from datetime import datetime
from base64 import b64decode, b64encode

from django.utils.encoding import smart_text
from django.conf import settings

import requests
from Crypto.Cipher import AES
from Crypto import Random

logger = logging.getLogger(__file__)

INSTA_FOLLOW_ORDERS_URL = f'{settings.INSTAFOLLOW_BASE_URL}/api/v1/instagram/orders/'


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


def get_insta_follow_token(insta_user_server_key):
    dt = datetime.utcnow()
    token = CryptoService(dt.strftime("%d%m%y%H") + dt.strftime("%d%m%y%H")).encrypt(str(insta_user_server_key))
    return f'Token {smart_text(token)}'


def get_insta_follow_order_by_action(instauser, action):
    url = f'{INSTA_FOLLOW_ORDERS_URL}'
    params = dict(page_size=5, action=action)

    logger.debug(
        f"[getting instafollow orders]-[URL: {url}]-[insta user id: {instauser.id}]-[params: {params}]"
    )
    # TODO needs to fill this field `server_key` here ??
    if not instauser.server_key:
        logger.warning(f'[insta user has no server key]-[insta user id: {instauser.id}]-[params: {params}]'
                       f'-[skipping this action...]')
        return

    # getting orders from api
    try:
        headers = dict(Authorization=get_insta_follow_token(instauser.server_key))
        response = requests.get(url, params=params, headers=headers)

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

    return response.json()
