import os
import requests

from tqdm import tqdm
from PIL import Image
from io import BytesIO
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from facemaps.data.database import Base, User, UserImage

# Database globals
engine = create_engine('sqlite:///instagram_users.db')
Base.metadata.bind = engine
session = sessionmaker(bind=engine)()

# Image settings
img_folder = 'faces_of_instagram'


def make_dir_if_not_exists(folder_name):
    """
    Makes folder
    """
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)


if __name__ == '__main__':
    make_dir_if_not_exists(img_folder)

    users = session.query(User).all()
    for _, u in enumerate(tqdm(users, desc='total users')):
        usr_img_urls = session.query(UserImage).filter(
            UserImage.user == u
        ).all()

        # Makes a folder for each instagram user
        cur_folder = os.path.join(img_folder, str(u.instagram_id))
        make_dir_if_not_exists(cur_folder)

        for idx, usr_img_url in enumerate(tqdm(usr_img_urls, desc=u.instagram_username)):
            r = requests.get(usr_img_url.url)
            img = Image.open(BytesIO(r.content))
            img_path = os.path.join(cur_folder, '{}.jpg'.format(idx))
            img.save(img_path, "JPEG")
