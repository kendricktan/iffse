import h5py
import random

from facemaps.data.database import FacialEmbeddings

from annoy import AnnoyIndex
from config import CONFIG


def get_shortcode_from_facialembeddings_id(fe_id):
    return FacialEmbeddings.get(id=fe_id).op.shortcode


# Tree settings
annoy_settings = CONFIG['annoy_tree_settings']
tree = AnnoyIndex(128, metric=annoy_settings['metric'])
tree.load(CONFIG['annoy_tree'])

# Random seed index
seed_idx = random.randint(0, len(FacialEmbeddings.select()))

print(
    'Original search: https://www.instagram.com/p/{}/'.format(get_shortcode_from_facialembeddings_id(seed_idx))
)
print('---' * 10)
print('Similar faces:')
idxs = tree.get_nns_by_item(seed_idx, 32)
shortcodes_unique = []
for i in idxs[1:]:
    s_ = get_shortcode_from_facialembeddings_id(i)
    if s_ not in shortcodes_unique:
        shortcodes_unique.append(s_)

for s in shortcodes_unique:
    print('https://www.instagram.com/p/{}/'.format(s))
