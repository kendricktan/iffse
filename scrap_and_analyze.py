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
import h5py

import sys
import dlib

import torch
import torch.nn as nn
import torch.nn.functional as F

import torchvision.transforms as transforms

import skimage.io as skio
import skimage.draw as skdr
import numpy as np

from peewee import OperationalError

from torch.autograd import Variable

from facemaps.data.database import db, SelfiePost, FacialEmbeddings
from facemaps.utils.helpers import string_to_np, np_to_string
from facemaps.utils.ml.open_face import load_openface_net
from facemaps.utils.cv.faces import (
    align_face_to_template,
    maybe_face_bounding_box,
    get_68_facial_landmarks
)

from io import BytesIO
from PIL import Image
from multiprocessing import Pool, Queue

# Global vars
# Headers to mimic mozilla
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

# Network to get embeddings
pyopenface = load_openface_net(
    './pretrained_weights/openface.pth', cuda=False).eval()

# Dlib to preprocess images
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(
    './pretrained_weights/shape_predictor_68_face_landmarks.dat'
)

transform = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ]
)


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
    r = requests.get(en_commons_url, headers=HEADERS)

    # Has multiple ways of passing query id
    # (They using a nightly build...)
    query_id = re.findall(r'c="(\d+)",l="TAG_MEDIA_UPDATED"', r.text)
    if len(query_id) == 0:
        query_id = re.findall(
            r'byTagName.get\(t\).pagination},queryId:"(\d+)",queryParams', r.text)
    query_id = query_id[0]

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
G
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
               'tag_name={}&first=6&after={}'.format(
                   query_id, tag_name, end_cursor)

    r = requests.get(feed_url, headers=HEADERS)
    r_js = json.loads(r.text)

    # Has next page or nah
    page_info = r_js['data']['hashtag']['edge_hashtag_to_media']['page_info']
    end_cursor = page_info['end_cursor']

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
        'https://www.instagram.com/explore/tags/{}/'.format(tag_name),
        headers=HEADERS)
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
    end_cursor = page_info['end_cursor']

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

    shortcode, display_url = args

    try:
        # Facial recognition logic here:
        # Download copy of image
        # Convert RGB and then to numpy
        r = requests.get(display_url, headers=HEADERS)
        img = Image.open(BytesIO(r.content)).convert("RGB")
        img = np.array(img)

        # Get bounding box
        bb = maybe_face_bounding_box(detector, img)

        if bb is None:
            print("[{}] No faces: {}".format(time.ctime(), shortcode))
            return

        # Iterate through each possible bounding box
        img_tensor = None
        for idx, b in enumerate(bb):
            # Get 68 landmarks
            points = get_68_facial_landmarks(predictor, img, b)

            # Realign image and resize
            # to 96 x 96 (network input)
            img_aligned = align_face_to_template(img, points, 96)

            # Convert to temporary tensor
            img_tensor_temp = transform(img_aligned)
            img_tensor_temp = img_tensor_temp.view(1, 3, 96, 96)

            # Essentially makes a 'batch' size
            if img_tensor is None:
                img_tensor = img_tensor_temp

            else:
                img_tensor = torch.cat((img_tensor, img_tensor_temp), 0)

        # Create a selfie post
        # attach all latent space to this foreign key
        s = SelfiePost(shortcode=shortcode, img_url=display_url)
        s.save()

        # Pass through network
        # get NUM_FACES x 128 latent space
        np_features = pyopenface(Variable(img_tensor))[0].data.numpy()

        for np_feature in np_features:
            # Convert to string and store in db
            np_str = np_to_string(np_feature)
            fe = FacialEmbeddings(op=s, latent_space=np_str)
            fe.save()

        print("[{}] Success: {}".format(time.ctime(), shortcode))

    except Exception as e:
        print("[{}] ====> Failed: {}, {}".format(time.ctime(), shortcode, e))


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
    try:
        db.connect()
        db.create_tables([SelfiePost, FacialEmbeddings])

    except OperationalError:
        pass

    p = Pool()

    # sds: Shortcodes, display_srcs
    # qid: query_id
    # ec : end cursor
    # itn: iterations needed
    sds, qid, ec, itn = instagram_hashtag_seed()

    while True:
        # Async map through all given shortcodes
        p.map_async(mp_instagram_hashtag_feed_to_queue, sds)

        # Get next batch
        sds, qid, ec = maybe_get_next_instagram_hashtag_feed(qid, ec)
        time.sleep(random.random() * 2)

    # Wait for pool to close
    p.close()
    p.join()
