import sys
import dlib

import skimage.io as skio
import skimage.draw as skdr

import numpy as np

from PIL import Image

from facemaps.cv.faces import align_face_to_template

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(
    './pretrained/shape_predictor_68_face_landmarks.dat')


def maybe_face_bounding_box(img):
    """
    Returns a bounding box if it finds
    ONE face. Any other case, it returns
    none
    """
    global detector

    dets = detector(img, 1)
    if len(dets) == 1:
        return dets[0]
    return None


def get_68_facial_landmarks(img, bb):
    """
    Returns a list of 68 facial landmarks

    Args:
        img: input image
        bb: bounding box containing the face
    """
    global predictor

    points = predictor(img, bb)
    return list(map(lambda p: (p.x, p.y), points.parts()))


img = skio.imread(sys.argv[1])

bb = maybe_face_bounding_box(img)
if bb is None:
    print('No faces found, exiting.')
    exit(0)

print('Found a face')
points = get_68_facial_landmarks(img, bb)
img_aligned = align_face_to_template(img, points, 256)

Image.fromarray(img_aligned, 'RGB').show()
