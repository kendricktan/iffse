import h5py
import random

from annoy import AnnoyIndex
from config import CONFIG

# h5py file
h5_file = h5py.File(CONFIG['hdf5'], 'r')
facial_embeddings = h5_file['facial_embeddings']
shortcodes = h5_file['shortcode']

seed_idx = random.randint(0, len(facial_embeddings))

tree = AnnoyIndex(128, metric='euclidean')
tree.load(CONFIG['annoy_tree'])

print('Original search: https://www.instagram.com/p/{}/'.format(shortcodes[seed_idx][0]))
print('---' * 10)
print('Similar faces:')
idxs = tree.get_nns_by_item(seed_idx, 32)
shortcodes_unique = []
for i in idxs[1:]:
    s_ = shortcodes[i][0]
    if s_ not in shortcodes_unique:
        shortcodes_unique.append(s_)

for s in shortcodes_unique:
    print('https://www.instagram.com/p/{}/'.format(s))
