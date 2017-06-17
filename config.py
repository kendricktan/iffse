import os

origin = os.path.abspath(os.path.dirname(__file__))
data_folder = os.path.join(origin, 'data')


CONFIG = {
    'annoy_tree': os.path.join(data_folder, 'annoy_selfiers.ann'),
    'sqlite_db': os.path.join(data_folder, 'selfiers.db'),
    'hdf5': os.path.join(data_folder, 'selfiers.hdf5')
}
