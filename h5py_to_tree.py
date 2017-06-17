import h5py

from annoy import AnnoyIndex
from tqdm import tqdm

# Our facialembeddings
h5_file = h5py.File('selfiers.hdf5', 'r')
facial_embeddings = h5_file['facial_embeddings']

# Build annoy tree
tree = AnnoyIndex(128, metric='euclidean')

for idx, fe in enumerate(tqdm(facial_embeddings)):
    tree.add_item(idx, fe)

tree.build(512)
tree.save('tree.ann')
