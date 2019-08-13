import numpy as np

def create_schwarzp(init_x, end_x, init_y, end_y, init_z, end_z, sx=256, sy=256, sz=256):
    z, y, x = np.ogrid[
        init_z : end_z : complex(0, sz),
        init_y : end_y : complex(0, sy),
        init_x : end_x : complex(0, sx),
    ]
    return np.cos(x) + np.cos(y) + np.cos(z)


def create_schwarzd(init_x, end_x, init_y, end_y, init_z, end_z, sx=256, sy=256, sz=256):
    z, y, x = np.ogrid[
        init_z : end_z : complex(0, sz),
        init_y : end_y : complex(0, sy),
        init_x : end_x : complex(0, sx),
    ]
    return np.sin(x)*np.sin(y)*np.sin(z) + np.sin(x)*np.cos(y)*np.cos(z) + np.cos(x)*np.sin(y)*np.cos(z) + np.cos(x)*np.cos(y)*np.sin(z)
