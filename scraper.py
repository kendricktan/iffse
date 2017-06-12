"""
" Scraps instagram username and their respective images
" into a sqlite3 database
"""
import logging
import sys
import os
import time
import random

from facemaps.insta_scraper import InstagramAPI
from facemaps.data.database import Base, User, UserImage
from tqdm import tqdm
from datetime import datetime
from pprint import pprint

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database globals
engine = create_engine('sqlite:///instagram_users.db')
Base.metadata.bind = engine
global_session = sessionmaker(bind=engine)()

# Instagram API globals
insta_usr = os.environ.get('insta_usr', '')
insta_pwd = os.environ.get('insta_pwd', '')

insta_api = InstagramAPI(insta_usr, insta_pwd)
insta_api.login()

# Logging
global_logger = logging.getLogger('scraper')
hdlr = logging.FileHandler('./scrap_errors.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
global_logger.addHandler(hdlr)
global_logger.setLevel(logging.WARNING)


def user_scrapped(user_id):
    """
    Checks if user has been scraped or not
    """
    global global_session
    return not (global_session.query(User).filter(User.instagram_id == user_id).first() is None)


def add_user(user_id, user_username):
    """
    Adds user to the database

    Returns created user object
    """
    global global_session
    new_user = User(instagram_id=user_id, instagram_username=user_username)
    global_session.add(new_user)
    global_session.commit()
    return new_user


def add_user_image(img_url, user):
    """
    Adds user image object to database

    Returns created user image object
    """
    global global_session
    new_user_image = UserImage(url=img_url, user=user)
    global_session.add(new_user_image)
    global_session.commit()
    return new_user_image


def get_user_followings(user_id):
    """
    Returns a list of users followings
    in tuple form: (user_id, username)
    """
    global insta_api

    user_followers = []

    next_max_id = ''
    while True:
        # Invoke instagram API to
        # get user followings
        insta_api.getUserFollowings(
            user_id,
            maxid=next_max_id
        )
        # Get next batch of users
        next_max_id = insta_api.LastJson.get('next_max_id', '')
        cur_users = insta_api.LastJson.get('users', [])

        # Format it so its a nice tuple :)
        cur_users_tuple = list(
            map(lambda x: (x['pk'], x['username']), cur_users)
        )

        user_followers.extend(cur_users_tuple)

        if not next_max_id:
            break

    return user_followers


def get_user_image_urls(user_items, width=480):
    """
    Returns list of urls when that matches the width

    Args:
        user_items: InstagramAPI.LastJson['items'] after calling getUserFeed
    """
    img_urls = []

    for i in user_items:
        for img_ver in i['image_versions2']['candidates']:
            if img_ver['width'] != width:
                continue
            img_urls.append(img_ver['url'])
            break

    return img_urls


def recursively_scrap_user_followings(user_id):
    """
    Recursively scraps pictures from a user and
    their respective followers (should in theory reach everyone in the world)
    (Start with own user id)
    """
    global insta_api

    # Get respetive users followings
    insta_api.getUsernameInfo(user_id)
    username = insta_api.LastJson['user']['username']
    followings = get_user_followings(user_id)

    max_idx = len(followings)
    for idx, (c_user_id, c_username) in enumerate(tqdm(followings, desc='{} followings'.format(username))):
        try:
            if user_scrapped(c_user_id):
                continue

            user_db = add_user(c_user_id, c_username)

            # Iterate through users feed
            feed_max_id = ''
            for _ in tqdm(range(10), desc='{} [{}/{}]'.format(c_username, idx, max_idx)):
                insta_api.getUserFeed(c_user_id, feed_max_id)
                feed_max_id = insta_api.LastJson.get('next_max_id', '')

                # If no items then its a private user
                if 'items' in insta_api.LastJson:
                    user_imgs = insta_api.LastJson['items']

                    img_urls = get_user_image_urls(user_imgs)
                    for url in img_urls:
                        add_user_image(url, user_db)

                    if not feed_max_id:
                        break

                    # Sleeps for 0 - 2.5 seconds randomly
                    time.sleep(random.random() * 2.5)

            # Sleeps for 3-5 seconds
            time.sleep(random.randint(3, 5))

        except Exception as e:
            global_logger.error(str(e))

    for idx, (c_user_id, c_username) in enumerate(followings):
        try:
            recursively_scrap_user_followings(c_user_id)
            time.sleep(random.randint(3, 5))
        except Exception as e:
            global_logger.error(str(e))


if __name__ == '__main__':
    recursively_scrap_user_followings(insta_api.username_id)
