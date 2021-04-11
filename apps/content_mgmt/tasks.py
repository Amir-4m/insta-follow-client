import os

from datetime import datetime

from celery import shared_task

from apps.insta_users.utils.instagram import get_action_session


@shared_task
def change_profile_pic(insta_user, profile_pic):
    session = get_action_session(insta_user)

    url = "https://www.instagram.com/accounts/web_change_profile_picture/"

    files = {'profile_pic': open(profile_pic.profile_picture.path, 'rb')}
    values = {"Content-Disposition": "form-data", "name": "profile_pic", "filename": "profilepic.jpg",
              "Content-Type": "image/jpeg"}

    return session.post(url, files=files, data=values)


@shared_task
def post_pic(insta_user, picture, caption):
    session = get_action_session(insta_user)

    microtime = int(datetime.now().timestamp())
    pic_size = os.path.getsize(picture.post_picture.path)
    headers = {
        "content-type": "image / jpg",
        "X-Entity-Name": f"fb_uploader_{microtime}",
        "Offset": "0",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
        "x-entity-length": f"{pic_size}",
        "X-Instagram-Rupload-Params": f'{{"media_type": 1, "upload_id": {microtime}, "upload_media_height": 800, "upload_media_width": 1000}}',
        'Referer': 'https://www.instagram.com/create/crop/',
    }
    session.headers.update(headers)
    session.post(f'https://www.instagram.com/rupload_igphoto/fb_uploader_{microtime}', data=open(picture.post_picture.path, "rb"))

    body = {
        'upload_id': f'{microtime}',
        "caption": caption,
        'custom_accessibility_caption': '',
        'retry_timeout': '',
    }
    session.headers.update({'Referer': 'https://www.instagram.com/create/details/'})
    session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
    return session.post('https://www.instagram.com/create/configure/', data=body)
