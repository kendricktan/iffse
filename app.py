import base64
import os
import jinja2
import requests
import argparse

from io import BytesIO

from tqdm import tqdm
from sanic import Sanic, response

from annoy import AnnoyIndex
from config import CONFIG

from iffse.utils.helpers import string_to_np, np_to_string
from iffse.data.database import FacialEmbeddings, SelfiePost
from scrapper import (
    get_instagram_shared_data,
    img_url_to_latent_space,
    img_url_to_pillow
)

# Global vars
app = Sanic(__name__)
app.static('/favicon.ico', './static/favicon.ico')
app.static('/sadbaby', './static/sadbaby.jpg')

annoy_settings = CONFIG['annoy_tree_settings']
annoy_tree = AnnoyIndex(128, metric=annoy_settings['metric'])

# Helper functions


def get_shortcode_from_facialembeddings_id(fe_id):
    """
    Returns a shortcode given from the
    facial embedding index from annoy tree
    Indexes start from 0, ids from db start from 1,
    hence + 1
    """
    return FacialEmbeddings.get(id=(fe_id + 1)).op.shortcode


def get_unique_shortcodes_from_fe_ids(fe):
    """
    Args:
        fe: facial embedding vector

    Returns:
        Shortcodes for the corresponding indexes
    """
    global annoy_tree

    idxs = annoy_tree.get_nns_by_vector(fe, 20)

    shortcodes_unique = []
    for i in idxs:
        s_ = get_shortcode_from_facialembeddings_id(i)
        if s_ not in shortcodes_unique:
            shortcodes_unique.append(s_)

    return shortcodes_unique


def pillow_to_base64(pil_img):
    """
    Converts pillow image to base64
    so it can be sent back withou refreshing
    """
    img_io = BytesIO()
    pil_img.save(img_io, 'PNG')
    return base64.b64encode(img_io.getvalue())


def render_jinja2(tpl_path, context):
    """
    Render jinja2 html template (not used lol)
    """
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


# Application logic
@app.route('/')
async def iffse_index(request):
    html_ = render_jinja2('./templates/index.html', {'WHAT': 'niggas'})
    return response.html(html_)


@app.route('/search', methods=["POST", ])
async def iffse_search(request):
    try:
        url = request.json.get('url', None)

        if url is None:
            return response.json({'url': 'need to specify instagram url'}, status=400)

        # Get instagram json data
        # (in order to get img url and stuff)
        url = 'https://www.instagram.com/p/{}/'.format(url)

        r = requests.get(url)
        r_js = get_instagram_shared_data(r.text)

        # Get display url and shortcode
        media_json = r_js['entry_data']['PostPage'][0]['graphql']['shortcode_media']
        display_src = media_json['display_url']
        shortcode = media_json['shortcode']

        # Pass image into the NN and
        # get the 128 dim embeddings
        np_features, img, bb = img_url_to_latent_space(display_src)

        # See if post has been indexed before
        s, created = SelfiePost.get_or_create(
            shortcode=shortcode, img_url=display_src)

        # If it hasn't been indexed before, then
        # add the latent embeddings into it
        if not created:
            for np_feature in np_features:
                # Convert to string and store in db
                np_str = np_to_string(np_feature)

                fe = FacialEmbeddings(op=s, latent_space=np_str)
                fe.save()

        # Now we can query it
        # For each face too
        shortcodes = {}
        for idx, feature in enumerate(np_features):
            b = bb[idx]

            # Crop to specific face
            lrtp = (b.left(), b.top(), b.right(), b.bottom())
            img_cropped = img.crop(lrtp)
            img_base64 = pillow_to_base64(img_cropped)

            # Get unique shortcode based on the features provided
            shortcodes_unique = get_unique_shortcodes_from_fe_ids(feature)
            shortcodes[idx] = {
                'face': img_base64,
                'shortcodes': shortcodes_unique
            }

        return response.json(
            {'data': shortcodes}
        )

    except Exception as e:
        print(e)
        return response.json(
            {'error': 'something fucked up lol'},
            status=400
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IFFSE')
    parser.add_argument('--rebuild-tree', action='store_true')
    args, unknown = parser.parse_known_args()

    # If specified to rebuild tree then rebuild it
    if args.rebuild_tree:
        print('Rebuidling tree...')
        for idx, f in enumerate(tqdm(FacialEmbeddings.select())):
            try:
                cur_np = string_to_np(f.latent_space)
                annoy_tree.add_item(idx, cur_np)

            except Exception as e:
                tqdm.write(str(e))

        annoy_tree.build(annoy_settings['forest_trees_no'])
        annoy_tree.save(CONFIG['annoy_tree'])

    # Else just load config
    else:
        annoy_tree.load(CONFIG['annoy_tree'])

    app.run(host='127.0.0.1', port=8000, debug=False)
