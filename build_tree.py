import numpy as np

from facemaps.utils.helpers import string_to_np
from facemaps.data.database import db, SelfiePost, FacialEmbeddings

from annoy import AnnoyIndex
from tqdm import tqdm

from config import CONFIG

# Annoy tree settings
annoy_settings = CONFIG['annoy_tree_settings']

# Annoy tree
tree = AnnoyIndex(128, metric=annoy_settings['metric'])

# Don't wanna store entire db into memory
for idx, f in enumerate(tqdm(FacialEmbeddings.select())):
    # Sqlte errors sometimes?
    try:
        cur_np = string_to_np(f.latent_space)
        cur_sc = f.op.shortcode

        tree.add_item(idx, cur_np)

    except Exception as e:
        tqdm.write(str(e))

tree.build(annoy_settings['forest_trees_no'])
tree.save(CONFIG['annoy_tree'])
