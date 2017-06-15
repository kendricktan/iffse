import dlib

import skimage.io as skio
import skimage.draw as skdr

import numpy as np

from PIL import Image

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('./pretrained/shape_predictor_68_face_landmarks.dat')

img = skio.imread('/home/kendrick/Pictures/face01.jpg')

dets = detector(img, 1)

for idx, d in enumerate(dets):
    y = np.array([d.top(), d.top(), d.bottom(), d.bottom()])
    x = np.array([d.left(), d.right(), d.right(), d.left()])

    rr, cc = skdr.polygon_perimeter(y, x, img.shape)
    img[rr, cc] = 1

    # Get the landmarks/parts for the face in box d.
    # 68 land marks
    shape = predictor(img, d)
    for i in range(68):
        rr, cc = skdr.circle(shape.part(i).y, shape.part(i).x, 3)
        img[rr, cc] = 255

Image.fromarray(img, 'RGB').show()
