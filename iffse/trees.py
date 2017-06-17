import numpy as np

from helpers import string_to_np

from annoy import AnnoyIndex
from tqdm import tqdm


def build_annoy_tree(facial_embeddings, tree_path,
                    annoy_metric='euclidean', annoy_trees_no=256):
    """
    Builds an annoy tree

    Args:
        facial_embeddings: List of facial embeddings to be indexed in tree
        tree_path: where the annoy tree will be saved
        annoy_metric: euclidean / angular
        annoy_tree_no: how many trees in the annoy forest? Larger = more accurate
    """

    # Annoy tree
    tree = AnnoyIndex(128, metric=annoy_metric)

    # Don't wanna store entire db into memory
    for idx, f in enumerate(tqdm(facial_embeddings)):
        # Sqlte errors sometimes?
        try:
            cur_np = string_to_np(f.latent_space)

            tree.add_item(idx, cur_np)

        except Exception as e:
            tqdm.write(str(e))

    tree.build(annoy_trees_no)
    tree.save(tree_path)
