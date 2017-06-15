"""
Instagram selfie scraper, date: 2017/06/14
Author: Kendrick Tan
"""
import threading
import time
import json
import re
import requests
import random

from multiprocessing import Pool, Queue

# Global queue
g_queue = Queue()


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


def get_instagram_hashtag_feed(query_id, end_cursor, tag_name='selfie'):
    """
    Traverses through instagram's hashtag feed, using the
    graphql endpoint
    """
    feed_url = 'https://www.instagram.com/graphql/query/?query_id={}&' \
               'tag_name={}&first=9&after={}'.format(
                   query_id, tag_name, end_cursor)

    r = requests.get(feed_url)
    r_js = json.loads(r.text)

    # Has next page or nah
    page_info = r_js['data']['hashtag']['edge_hashtag_to_media']['page_info']
    end_cursor = page_info['has_next_page']

    edges = r_js['data']['hashtag']['edge_hashtag_to_media']['edges']

    display_srcs = []
    shortcodes = []

    for e in edges:
        shortcodes.append(e['node']['shortcode'])
        display_srcs.append(e['node']['display_url'])

    return list(zip(shortcodes, display_srcs)), end_cursor


def instagram_hashtag_seed(tag_name='selfie'):
    """
    Seed function that calls instagram's hashtag page
    in order to obtain the end_cursor thingo
    """
    r = requests.get(
        'https://www.instagram.com/explore/tags/{}/'.format(tag_name))
    r_js = get_instagram_shared_data(r.text)

    # To get the query id
    en_common_js_url = get_instagram_us_common_js(r.text)
    query_id = get_instagram_feed_page_query_id(en_common_js_url)

    # Concat first 12 username and profile_ids here
    shortcodes = []
    display_srcs = []

    # Fb works by firstly calling the first page
    # and loading the HTML and all that jazz, so
    # you need to parse that bit during the 1st call.
    # The proceeding images can be obtained by
    # calling the graphql api endpoint with a
    # specified end_cursor
    media_json = r_js['entry_data']['TagPage'][0]['tag']['media']
    for m in media_json['nodes']:
        shortcodes.append(m['code'])
        display_srcs.append(m['display_src'])

    page_info = media_json['page_info']
    end_cursor = page_info['has_next_page']

    # How many times do we need to scroll through
    # 9 photos at a time to get every single feed
    # Algo: (count - 12) / 12
    # 12 images during first req and 12  for the proceeding
    media_count = media_json['count']
    iterations_needed = int((media_count - 12) / 12)

    return list(zip(shortcodes, display_srcs)), query_id, end_cursor, iterations_needed


def mp_instagram_hashtag_feed_to_queue(args):
    """
    Multiprocessing function for scraping instagram hashtag feed

    Returns:
        (Success, shortcodes, display_srcs)
    """
    global g_queue

    shortcodes, display_srcs = args

    try:
        # Do facial recognition here:
        # 1. Find if there's > 1 face, if there's > 1 face, discard
        # 2. Reorientated face
        # 3. Save a copy of the urls and whatnot
        pass

    except Exception as e:
        return False, shortcodes, display_srcs, e

    return True, shortcodes, display_srcs, 0


def maybe_get_next_instagram_hashtag_feed(qid, ec):
    """
    Trys to get instagram hashtag feed, it it can't
    changes query id and calls itself again
    """
    try:
        sds, ec = get_instagram_hashtag_feed(qid, ec)

    except Exception as e:
        print('!!!! Error: {} !!!!'.format(e))
        print('!!!! Instagram probably rate limited us... whoops !!!!')
        print('!!!! Pausing for 3-5 minutes !!!!')
        time.sleep(random.randint(180, 300))

        # Get new query id
        _, new_qid, _, _ = instagram_hashtag_seed()

        # Calls itself infinitely until it returns
        # #untested
        return maybe_get_next_instagram_hashtag_feed(new_qid, ec)

    return sds, qid, ec


if __name__ == '__main__':
    p = Pool()

    # sds: Shortcodes, display_srcs
    # qid: query_id
    # ec : end cursor
    # itn: iterations needed
    sds, qid, ec, itn = instagram_hashtag_seed()

    sc_dp_json = {}
    for idx in range(1, 5):
        # success, shortcodes, display src, latent value
        for s_, sc_, dp_, lv_ in p.imap_unordered(mp_instagram_hashtag_feed_to_queue, sds):

            if s_:
                print("[{}] Success: {}".format(time.ctime(), sc_))
                sc_dp_json[sc_] = dp_

            else:
                print("[{}] ====> Failed: {}".format(time.ctime(), sc_))

        # Get next batch
        sds, qid, ec = maybe_get_next_instagram_hashtag_feed(qid, ec)
        time.sleep(random.random() * 2)

    with open('data.json', 'w') as f:
        json.dump(sc_dp_json, f)
