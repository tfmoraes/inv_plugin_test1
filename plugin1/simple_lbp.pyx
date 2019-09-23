# distutils: language = c++

import numpy as np
cimport numpy as np
cimport cython
from cython.parallel import prange
from libcpp.vector cimport vector
from libcpp cimport bool

ctypedef fused image_t:
    np.int16_t
    np.uint8_t

@cython.boundscheck(False) # turn of bounds-checking for entire function
@cython.cdivision(True)
@cython.wraparound(False)
def cy_simple_lbp(image_t[:, :, :] image, np.uint32_t[:, :, :] out):
    cdef np.uint32_t value = 0
    cdef np.uint32_t step = 0
    cdef int x, y, z
    cdef int dx, dy, dz
    cdef int lx, ly, lz
    dz = image.shape[0]
    dy = image.shape[1]
    dx = image.shape[2]

    for z in range(dz):
        for y in range(dy):
            for x in range(dx):
                step = 0
                for lz in range(z-1, z+2):
                    for ly in range(y-1, y+2):
                        for lx in range(x-1, x+2):
                            if 0 <= lz < dz and 0 <= ly < dy and 0 <= lx < dx:
                                if image[z, y, x] < image[lz, ly, lx]:
                                    out[z, y, x] = out[z, y, x] | (1<<step)
                            step += 1



def simple_lbp(np.ndarray[image_t, ndim=3] image):
    cdef np.ndarray[np.uint32_t, ndim=3] out = np.zeros_like(image, dtype=np.uint32)
    cy_simple_lbp(image, out)
    print(np.unique(out))
    return out


def test_2():
    cdef vector[bool] manolo
    manolo.push_back(True)
    manolo.push_back(False)
    manolo.push_back(False)
    manolo.push_back(True)

    return manolo
