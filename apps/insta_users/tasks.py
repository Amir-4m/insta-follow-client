import logging
import os

from celery.schedules import crontab
from celery.task import periodic_task
from celery import shared_task
from pid import PidFile

from .models import InstaUser
from .utils.insta_follow import insta_follow_register, insta_follow_get_orders, insta_follow_order_done
from .utils.instagram import instagram_login, instagram_follow

logger = logging.getLogger(__name__)


# TODO: for later use
"""
INSTAGRAM_HEADERS = {
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
"""


def check_running(function_name):
    if not os.path.exists('/tmp'):
        os.mkdir('/tmp')
    file_lock = PidFile(str(function_name), piddir='/tmp')
    try:
        file_lock.create()
        return file_lock
    except:
        return None


def stop_duplicate_task(func):
    def inner_function():
        file_lock = check_running(func.__name__)
        if not file_lock:
            logger.error(f"[Another {func.__name__} is already running]")
            return False
        func()
        if file_lock:
            file_lock.close()
        return True

    return inner_function


@periodic_task(run_every=crontab(minute='*'))
def p_insta_user_action():
    insta_user_action()


@stop_duplicate_task
def insta_user_action():
    insta_users = InstaUser.objects.live()
    for insta_user in insta_users:
        orders = insta_follow_get_orders(insta_user, 'follow')
        for order in orders:
            instagram_follow(insta_user, order)
            insta_follow_order_done(insta_user, order['id'])


@shared_task
def insta_follow_login_task(insta_user_id):
    insta_user = InstaUser.objects.get(id=insta_user_id)
    insta_follow_register(insta_user)


@shared_task
def instagram_login_task(insta_user_id):
    insta_user = InstaUser.objects.get(id=insta_user_id)
    instagram_login(insta_user)
