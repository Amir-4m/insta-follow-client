import logging
from datetime import datetime

import requests
from celery import shared_task

from .models import InstaUser

logger = logging.getLogger(__name__)

BASE_URL = "https://www.instagram.com/"
LOGIN_URL = BASE_URL + "accounts/login/ajax/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; ) Gecko/20100101 Firefox/65.0"

headers = {
    "Host": "www.instagram.com",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.instagram.com/accounts/edit/",
    "X-IG-App-ID": "936619743392459",
    "X-Requested-With": "XMLHttpRequest",
    "DNT": "1",
    "Connection": "keep-alive",
}
session = requests.Session()
session.headers = {'user-agent': USER_AGENT, 'Referer': BASE_URL}


@shared_task
def instagram_login(pk):
    try:
        usr = InstaUser.objects.get(id=pk)
        str_time = datetime.now().timestamp()
        pswd = f'#PWD_INSTAGRAM_BROWSER:0:{str_time}:{usr.password}'
        resp = session.get(BASE_URL)
        session.headers.update({'X-CSRFToken': resp.cookies['csrftoken']})
        login_data = {'username': usr.username, 'enc_password': pswd}
        login_resp = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        session.headers.update({'X-CSRFToken': resp.cookies['csrftoken']})
        if login_resp.json()['authenticated']:
            usr.session = str(session.cookies['sessionid'])
            usr.user_id = session.cookies['ds_user_id']
            usr.save()
            logger.info(f"log in succeeded with the credintial of [username: {usr.username} -- password: {usr.password}]")
    except Exception as e:
        logger.error(f"log in failed with the credintial of [username: {usr.username} -- password: {usr.password}]")
