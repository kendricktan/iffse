"""
Instagram selfie scraper, date: 2017/06/14
Author: Kendrick Tan
"""
import time
import json
import re
import requests
import random

from tqdm import tqdm
from multiprocessing import Pool


def get_instagram_profile_page_query_id(en_commons_url):
    """
    Given the en_US_Commons.js url, find the query
    id from within for a profile page

    Args:
        en_commons_url: URL for the en_Commons_url.js
                        (can be found by viewing instagram.com source)

    Returns:
        query_id needed to query graphql
    """
    r = requests.get(en_commons_url)
    query_id = re.findall(r'l="(\d+)",p="PROFILE_POSTS_UPDATED"', r.text)[0]

    return query_id


def get_instagram_feed_page_query_id(en_commons_url):
    """
    Given the en_US_Commons.js url, find the query
    id from within for a feed page

    Args:
        en_commons_url: URL for the en_Commons_url.js
                        (can be found by viewing instagram.com source)

    Returns:
        query_id needed to query graphql
    """
    r = requests.get(en_commons_url)
    query_id = re.findall(r'c="(\d+)",l="TAG_MEDIA_UPDATED"', r.text)[0]

    return query_id


def get_instagram_us_common_js(text):
    """
    Given a Instagram HTML page, return the
    en_US_Common.js thingo URL (contains the query_id)

    Args:
        text: Raw html source for instagram.com

    Returns:
        url to obtain us_commons_js
    """
    js_file = re.findall(r"en_US_Commons.js/(\w+).js", text)[0]
    return "https://www.instagram.com/static/bundles/en_US_Commons.js/{}.js".format(str(js_file))


def get_instagram_shared_data(text):
    """
    Given a Instagram HTML page, return the
    'shared_data' json object

    Args:
        text: Raw html source for instagram

    Returns:
        dict containing the json blob thats in
        instagram.com
    """
    json_blob = re.findall(r"window._sharedData\s=\s(.+);</script>", text)[0]
    return json.loads(json_blob)


def get_username_from_shortcode(shortcode):
    """
    Given a shortcode (e.g. 'BUwTJMRgKKD'), try and
    find op's username (in order to get their profile page)

    Args:
        shortcode: instagram shortcode (BUTJMRgKKd)

    Returns:
        OP's username
    """
    shortcode_url = 'https://www.instagram.com/p/{}/'.format(shortcode)

    r = requests.get(shortcode_url)
    r_js = get_instagram_shared_data(r.text)
    username = r_js['entry_data']['PostPage'][0]['graphql']['shortcode_media']['owner']['username']
    return username


def get_instagram_profile_next_end_cursor(query_id, profile_id, end_cursor, keywords=['selfie']):
    """
    Given the next endcursor, retrieve the list
    of profile pic URLS and if 'has_next_page'
    """
    next_url = "https://www.instagram.com/graphql/query/?query_id={}&id={}&first=12&after={}".format(
        query_id, profile_id, end_cursor)

    r = requests.get(next_url)
    r_json = json.loads(r.text)

    # Gets next page info
    # Try catch if there's no next page
    try:
        edge_timeline_media = r_json['data']['user']['edge_owner_to_timeline_media']
        page_info = edge_timeline_media['page_info']
        has_next_page, end_cursor = page_info['has_next_page'], page_info['end_cursor']
    except:
        return [], False, None

    # Accumulates all display pictures here
    display_pictures = []
    for i in edge_timeline_media['edges']:
        for keyword in keywords:
            # Try escape when there's no caption
            try:
                if keyword.lower() in i['node']['edge_media_to_caption']['edges'][0]['node']['text']:
                    display_pictures.append(i['node']['display_url'])
            except:
                pass

    return display_pictures, has_next_page, end_cursor


def get_instagram_profile_display_pictures(username, profile_id, keywords=['selfie'], max_pics=3):
    """
    Given an instagram username, traverse their profile
    and scrap <num_pics> of their display pictures

    Args:
        username:   Instagram username
        profile_id: Instagram profile_id
        keywords:   List of keywords. Scraps display_url if one of
                    the keyword is present in the photo caption
        max_pics:   Maximum number of pictures to get that contains
                    a keyword
    """
    # Total display images scraped
    total_display_images = []

    r = requests.get('https://www.instagram.com/{}/'.format(username))
    r_js = get_instagram_shared_data(r.text)
    media_json = r_js['entry_data']['ProfilePage'][0]['user']['media']

    # Unique query id for each profile view
    en_common_js_url = get_instagram_us_common_js(r.text)
    query_id = get_instagram_profile_page_query_id(en_common_js_url)

    # Get the first 12 display pictures
    # Only add them to database if they have
    # a 'selfie' caption
    for pic in media_json['nodes']:
        for keyword in keywords:
            # Try escape in case there's no caption
            try:
                if keyword.lower() in pic['caption'].lower():
                    total_display_images.append(pic['display_src'])
                    break
            except:
                pass

    # Next N pictures are a bit different
    end_cursor = media_json['page_info']['end_cursor']
    has_next_page = media_json['page_info']['has_next_page']

    # Only want to scrap entire feed, just want
    # to go through 81 photos (12 initial + 60 traversed)
    for i in range(6):
        display_images, has_next_page, end_cursor \
            = get_instagram_profile_next_end_cursor(query_id, profile_id, end_cursor)
        total_display_images.extend(display_images)

        if not has_next_page or len(total_display_images) > max_pics:
            break

    return username, profile_id, total_display_images


def mp_instagram_profile_display_pictures(args):
    """
    Multiprocessing function for get_instagram_profile_display_pictures
    """
    username, profile_id = args

    try:
        return get_instagram_profile_display_pictures(username, profile_id)
    except:
        return None, None, None


def get_instagram_hashtag_feed(query_id, end_cursor, tags='selfie'):
    """
    Traverses through instagram's hashtag feed, using the
    graphql endpoint
    """
    feed_url = 'https://www.instagram.com/graphql/query/?query_id={}&' \
               'tag_name={}&first=9&after={}'.format(
                   query_id, tags, end_cursor)

    r = requests.get(feed_url)
    r_js = json.loads(r.text)

    # Has next page or nah
    page_info = r_js['data']['hashtag']['edge_hashtag_to_media']['page_info']
    has_next_page, end_cursor = page_info['has_next_page'], page_info['end_cursor']

    edges = r_js['data']['hashtag']['edge_hashtag_to_media']['edges']

    usernames = []
    profile_ids = []
    for i in edges:
        profile_ids.append(i['node']['owner']['id'])
        usernames.append(
            get_username_from_shortcode(i['node']['shortcode'])
        )

    return list(zip(usernames, profile_ids)), has_next_page, end_cursor


def instagram_hashtag_seed(tags='selfie'):
    """
    Seed function that calls instagram's hashtag page
    in order to obtain the end_cursor thingo
    """
    r = requests.get('https://www.instagram.com/explore/tags/{}/'.format(tags))
    r_js = get_instagram_shared_data(r.text)

    # To get the query id
    en_common_js_url = get_instagram_us_common_js(r.text)
    query_id = get_instagram_feed_page_query_id(en_common_js_url)

    # Concat first 12 username and profile_ids here
    usernames = []
    profile_ids = []

    # Fb works by firstly calling the first page
    # and loading the HTML and all that jazz, so
    # you need to parse that bit during the 1st call.
    # The proceeding images can be obtained by
    # calling the graphql api endpoint with a
    # specified end_cursor
    media_json = r_js['entry_data']['TagPage'][0]['tag']['media']
    for i in media_json['nodes']:
        profile_ids.append(i['owner']['id'])
        usernames.append(get_username_from_shortcode(i['code']))

    page_info = media_json['page_info']
    has_next_page, end_cursor = page_info['has_next_page'], page_info['end_cursor']

    return list(zip(usernames, profile_ids)), query_id, has_next_page, end_cursor


if __name__ == '__main__':
    p = Pool()

    user_dps = {}

    # upl: username profile_id list
    # qid: query id
    # hnp: has next page
    # ec : end_cursor
    upl, qid, hnp, ec = instagram_hashtag_seed()
    for i in tqdm(range(10), desc='batch no.'):
        for username, profile_id, dps in p.imap_unordered(mp_instagram_profile_display_pictures, upl):
            if username is not None:
                tqdm.write('[!] Done: {} [{}] <{} images>'.format(username, profile_id, len(dps)))

        try:
            upl, hnp, ec = get_instagram_hashtag_feed(qid, ec)

        except:
            # Probably got rate limited by instagram?
            # Sleep for 5 minutes and resume
            # but refresh and get a new query id
            tqdm.write('[X] Probably rate limited by instagram, pausing for a random amount of time...')
            time.sleep(random.randint(300, 500))

            _, qid, _, _ = instagram_hashtag_seed()
            upl, hnp, ec = get_instagram_hashtag_feed(qid, ec)

        time.sleep(random.randint(3, 7))

    with open('data.json', 'w') as f:
        json.dump(user_dps, f)
