import numpy as np


def np_to_string(n):
    """
    Converts a one dimensional numpy array
    into a string format to be stored in db
    """

    # Squeeze out dims
    n = np.squeeze(n)

    return np.array_str(n)[1:-1]


def string_to_np(s):
    """
    Converts string to numpy array.
    """
    return np.fromstring(s, sep=' ')
