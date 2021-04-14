import time

from django.conf import settings

from apps.insta_users.utils.instagram import get_instagram_follow_suggested, get_instagram_session


def follow(session, user_id_to_follow):
    return session.post(f"https://www.instagram.com/web/friendships/{user_id_to_follow}/follow/")


def follow_suggested(instauser):
    user_session = get_instagram_session(instauser)

    users_to_follow = get_instagram_follow_suggested(instauser)[:settings.MAX_SUGGESTED_FOLLOW_EACH_TURN]
    for data in users_to_follow:
        time.sleep(.6)
        user_id = data['node']['user']['id']
        follow(user_session, user_id)
