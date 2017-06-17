import os

origin = os.path.abspath(os.path.dirname(__file__))
data_folder = os.path.join(origin, 'data')


CONFIG = {
    'annoy_tree': os.path.join(data_folder, 'annoy_selfiers.ann'),
    'annoy_tree_settings': {
        'metric': 'euclidean',  # euclidean / angular
        'forest_trees_no': 128  # Number a forest of N tr
    },
    # If you change sqlite_db, please reflect it in
    # ./facemaps/data/database.py
    'sqlite_db': os.path.join(data_folder, 'selfiers.db'),
}
