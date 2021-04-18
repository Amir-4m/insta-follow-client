import os
import random
from datetime import datetime

from celery import shared_task

from apps.content_mgmt.models import ImageContent, CaptionContent
from apps.insta_users.utils.instagram import get_instagram_session

from conf import settings


@shared_task
def change_profile_pic(insta_user):
    session = get_instagram_session(insta_user)

    content = ImageContent.objects.order_by('?')[0]

    files = {'profile_pic': open(f'{settings.MEDIA_ROOT}/{content.image}', 'rb')}
    values = {"Content-Disposition": "form-data", "name": "profile_pic", "filename": "profilepic.jpg",
              "Content-Type": "image/jpeg"}

    return session.post("https://www.instagram.com/accounts/web_change_profile_picture/", files=files, data=values)


@shared_task
def post_pic(insta_user):
    session = get_instagram_session(insta_user)

    content = ImageContent.objects.order_by('?')[0]
    height = content.image.height
    width =content.image.width

    caption = CaptionContent.objects.order_by('?')[0]

    microtime = int(datetime.now().timestamp())
    pic_size = content.image.size

    headers = {
        "content-type": "image/jpg",
        "X-Entity-Name": f"fb_uploader_{microtime}",
        "Offset": "0",
        "x-entity-length": f"{pic_size}",
        "X-Instagram-Rupload-Params": f'{{"media_type": 1, "upload_id": {microtime}, "upload_media_height": {height}, "upload_media_width": {width}}}',
    }
    session.headers.update(headers)
    session.post(f'https://www.instagram.com/rupload_igphoto/fb_uploader_{microtime}',
                 data=open(f'{settings.MEDIA_ROOT}/{content.image}', "rb"))

    body = {
        'upload_id': f'{microtime}',
        'caption': caption.caption,
        'custom_accessibility_caption': '',
        'retry_timeout': '',
    }
    session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
    return session.post('https://www.instagram.com/create/configure/', data=body)


def post_story(insta_user):
    session = get_instagram_session(insta_user)
    content = ImageContent.objects.order_by('?')[0]
    height = content.image.height
    width = content.image.width

    microtime = int(datetime.now().timestamp())
    pic_size = os.path.getsize(f'{settings.MEDIA_ROOT}/{content.image}')
    headers = {
        "content-type": "image / jpg",
        "X-Entity-Name": f"fb_uploader_{microtime}",
        "Offset": "0",
        "x-entity-length": f"{pic_size}",
        "X-Instagram-Rupload-Params": f'{{"media_type": 1, "upload_id": {microtime}, "upload_media_height": {height}, "upload_media_width": {width}}}',
    }
    session.headers.update(headers)
    session.post(f'https://www.instagram.com/rupload_igphoto/fb_uploader_{microtime}',
                 data=open(f'{settings.MEDIA_ROOT}/{content.image}', "rb"))

    body = {
        'upload_id': f'{microtime}',
        'custom_accessibility_caption': '',
        'retry_timeout': '',
    }
    session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
    return session.post('https://www.instagram.com/create/configure_to_story/', data=body)