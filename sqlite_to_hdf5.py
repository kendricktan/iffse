import h5py
import numpy as np

from tqdm import tqdm

from facemaps.utils.helpers import string_to_np
from facemaps.data.database import db, SelfiePost, FacialEmbeddings

# Our h5 database to be used with annoy
f = h5py.File('selfiers.hdf5', 'w')
sc = f.create_dataset('shortcode', (1, 1), maxshape=(None, 1), dtype=h5py.special_dtype(vlen=str))
fe = f.create_dataset('facial_embeddings', (1, 128), maxshape=(None, 128), dtype=np.dtype('float32'))

# Don't wanna store entire db into memory
idx = 0
for _, f in enumerate(tqdm(FacialEmbeddings.select())):
    try:
        cur_np = string_to_np(f.latent_space)
        cur_sc = f.op.shortcode

        sc.resize((idx + 1, 1))
        sc[idx] = cur_sc

        fe.resize((idx + 1, 128))
        fe[idx] = cur_np

        idx += 1
    except Exception as e:
        tqdm.write(str(e))
