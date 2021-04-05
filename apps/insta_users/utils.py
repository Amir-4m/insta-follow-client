import logging
from base64 import b64decode, b64encode
from datetime import datetime

from .models import InstaUser
from django.conf import settings
from django.utils.encoding import smart_text

import requests
from Crypto.Cipher import AES
from Crypto import Random

logger = logging.getLogger(__file__)

JSON_HEADERS = {'Content-type': 'application/json'}

LOGIN_VERIFICATION_URL = f'{settings.INSTAFOLLOW_BASE_URL}/api/v1/instagram/login-verification/'


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


def create_instafollow_crypto_token(insta_user_uuid):
    dt = datetime.utcnow()
    token = CryptoService(dt.strftime("%d%m%y%H") + dt.strftime("%d%m%y%H")).encrypt(str(insta_user_uuid))

    return f'Token {smart_text(token)}'


def get_instafollow_uuid(insta_user_id):
    # getting InstaUser object
    try:
        instauser = InstaUser.objects.get(id=insta_user_id)
    except InstaUser.DoesNotExist as e:
        logger.warning(f'[getting instafollow uuid failed]-[instauser id: {insta_user_id}]-[exc: {e}]')
        return

    # getting uuid from instafollow api
    parameter = dict(
        instagram_user_id=instauser.user_id,
        instagram_username=instauser.username,
        session_id=instauser.session
    )
    url = LOGIN_VERIFICATION_URL
    logger.debug(f"[calling api]-[URL: {url}]-[data: {parameter}]")

    try:
        response = requests.post(url, json=parameter, header=JSON_HEADERS)

    except requests.exceptions.HTTPError as e:
        logger.warning(
            f'[making request failed]-[response err: {e.response.text}]-[status code: {e.response.status_code}]'
            f'-[URL: {url}]-[exc: {e}]'
        )
        return
    except requests.exceptions.ConnectTimeout as e:
        logger.critical(f'[request failed]-[URL: {url}]-[exc: {e}]')
        return
    except Exception as e:
        logger.error(f'[request failed]-[URL: {url}]-[exc: {e}]')
        return

    instafollow_uuid = response.json().get('uuid')

    instauser.server_key = instafollow_uuid
    instauser.save()

    return instauser

