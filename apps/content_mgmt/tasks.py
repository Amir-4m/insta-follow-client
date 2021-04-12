import os

from datetime import datetime

import requests

from apps.insta_users.utils.instagram import get_action_session
from PIL import Image

from conf import settings


def change_profile_pic(insta_user, content):
    session = get_action_session(insta_user)

    url = "https://www.instagram.com/accounts/web_change_profile_picture/"

    img_file = os.path.join(f'{settings.MEDIA_ROOT}/{content.created_time}--temp.jpg')
    r = requests.get(content.image_url)
    open(img_file, 'wb').write(r.content)

    files = {'profile_pic': open(f'{settings.MEDIA_ROOT}/{content.created_time}--temp.jpg', 'rb')}
    values = {"Content-Disposition": "form-data", "name": "profile_pic", "filename": "profilepic.jpg",
              "Content-Type": "image/jpeg"}

    s = session.post(url, files=files, data=values)
    os.remove(f'{settings.MEDIA_ROOT}/{content.created_time}--temp.jpg')
    return s


def post_pic(insta_user, content):
    session = get_action_session(insta_user)

    img_file = os.path.join(f'{settings.MEDIA_ROOT}/{content.created_time}--temp.jpg')
    r = requests.get(content.image_url)
    open(img_file, 'wb').write(r.content)
    image = Image.open(f'{settings.MEDIA_ROOT}/{content.created_time}--temp.jpg')
    image.thumbnail((800, 1000), Image.ANTIALIAS)
    image.save(f'{settings.MEDIA_ROOT}/{content.created_time}--temp2.jpg', 'JPEG', quality=88)

    microtime = int(datetime.now().timestamp())
    pic_size = os.path.getsize(f'{settings.MEDIA_ROOT}/{content.created_time}--temp2.jpg')
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
    session.post(f'https://www.instagram.com/rupload_igphoto/fb_uploader_{microtime}',
                 data=open(f'{settings.MEDIA_ROOT}/{content.created_time}--temp2.jpg', "rb"))

    body = {
        'upload_id': f'{microtime}',
        'caption': content.caption,
        'custom_accessibility_caption': '',
        'retry_timeout': '',
    }
    session.headers.update({'Referer': 'https://www.instagram.com/create/details/'})
    session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
    s = session.post('https://www.instagram.com/create/configure/', data=body)
    os.remove(f'{settings.MEDIA_ROOT}/{content.created_time}--temp.jpg')
    os.remove(f'{settings.MEDIA_ROOT}/{content.created_time}--temp2.jpg')
    return s


# def post_vid():
#     insta_user = InstaUser.objects.first()
#     session = requests.session()
#     session.headers.update({'X-CSRFToken': insta_user.session['csrftoken']})
#     session.headers.update({'X-Instagram-AJAX': '7e64493c83ae'})
#     session.cookies.update(insta_user.session)
#
#     microtime = int(datetime.now().timestamp())
#     video = cv2.VideoCapture('vid.mp4')
#     frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
#     fps = video.get(cv2.CAP_PROP_FPS)
#     height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
#     width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
#
#     rupload_params = {
#         "retry_context": '{"num_step_auto_retry":0,"num_reupload":0,"num_step_manual_retry":0}',
#         "media_type": "2",
#         "xsharing_user_ids": "[]",
#         "upload_id": str(microtime),
#         "upload_media_duration_ms": str(int((frames / fps) * 1000)),
#         "upload_media_width": str(width),
#         "upload_media_height": str(height),
#
#     }
#
#     headers = {
#
#         "Accept-Encoding": "gzip",
#         "X-Instagram-Rupload-Params": json.dumps(rupload_params),
#         "X_FB_VIDEO_WATERFALL_ID": str(uuid4()),
#         "X-Entity-Type": "video/mp4",
#         "X-Entity-Name": f"{microtime}",
#         "Offset": "0",
#         "X-Entity-Length": str(int((frames / fps) * 1000)),
#         "Content-Type": "application/octet-stream",
#         "Content-Length": str(int((frames / fps) * 1000)),
#
#     }
#
#     session.headers.update(headers)
#
#     s = session.post(f"https://www.instagram.com/rupload_igvideo/{microtime}", data=open('vid.mp4', "rb").read())
#     print(s.status_code)
#     print(s.text)
#
#     vid_body = {
#         "upload_id": str(microtime),
#         "source_type": 2,
#         "poster_frame_index": 0,
#         "length": 0.00,
#         "audio_muted": False,
#         # "date_time_original": time.strftime("%Y:%m:%d %H:%M:%S", time.localtime()),
#         "timezone_offset": "10800",
#         "width": width,
#         "height": height,
#         "clips": [
#             {
#                 "length": str(int((frames / fps)) * 1000),
#                 "source_type": "2"
#             }
#         ],
#         "extra": {"source_width": width, "source_height": height},
#         "caption": "video done",
#     }
#
#     # session.headers.update(upload_headers)
#     s2 = session.post("https://api.instagram.com/v1/media/configure/?video=1", data=vid_body)
#     print(s2.status_code)
#     print(s2.text)
