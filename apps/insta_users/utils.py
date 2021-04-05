import logging
import requests

from datetime import datetime
from base64 import b64decode, b64encode

from .models import InstaUser
from django.conf import settings
from django.utils.encoding import smart_text

from Crypto.Cipher import AES
from Crypto import Random

logger = logging.getLogger(__file__)


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


def get_insta_follow_token(insta_user_server_key):
    dt = datetime.utcnow()
    token = CryptoService(dt.strftime("%d%m%y%H") + dt.strftime("%d%m%y%H")).encrypt(str(insta_user_server_key))
    return f'Token {smart_text(token)}'


def insta_follow_auth(insta_user_id):
    # getting InstaUser object
    try:
        insta_user = InstaUser.objects.get(id=insta_user_id)
    except InstaUser.DoesNotExist as e:
        logger.warning(f'[getting instafollow uuid failed]-[instauser id: {insta_user_id}]-[exc: {e}]')
        return

    # getting uuid from instafollow api
    parameter = dict(
        instagram_user_id=insta_user.user_id,
        instagram_username=insta_user.username,
        session_id=insta_user.session
    )
    url = LOGIN_VERIFICATION_URL
    logger.debug(f"[calling api]-[URL: {url}]-[data: {parameter}]")

    try:
        response = requests.post(url, json=parameter)
        insta_user.server_key = response.json().get('uuid')
        insta_user.save()
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

    return insta_user.server_key

