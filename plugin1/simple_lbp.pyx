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
cdef void _cy_simple_lbp(image_t[:, :, :] image, np.uint8_t[:, :, :, :] out) nogil:
    cdef int[8][2] positions
    cdef int[8] powers
    cdef int x, y, z
    cdef int dx, dy, dz
    cdef int lx, ly, lz
    cdef unsigned char i = 0
    positions[0][0] =  -1  ; positions[0][1] =  1
    positions[1][0] =  0  ; positions[1][1] =  1
    positions[2][0] =  1  ; positions[2][1] = 1
    positions[3][0] =  1  ; positions[3][1] = 0
    positions[4][0] =  1  ; positions[4][1] = -1
    positions[5][0] = 0  ; positions[5][1] =  -1
    positions[6][0] = -1  ; positions[6][1] =  -1
    positions[7][0] =  -1  ; positions[7][1] =  0
    powers[0] = 1
    powers[1] = 2
    powers[2] = 4
    powers[3] = 8
    powers[4] = 16
    powers[5] = 32
    powers[6] = 64
    powers[7] = 128
    dz = image.shape[0]
    dy = image.shape[1]
    dx = image.shape[2]

    for z in prange(dz):
        for y in range(dy):
            for x in range(dx):
                out[z, y, x, 0] = 0
                out[z, y, x, 1] = 0
                out[z, y, x, 2] = 0
                for i in range(8):
                    # AXIAL
                    lx = x + positions[i][0]
                    ly = y + positions[i][1]
                    lz = z
                    if lz >= 0 and lz < dz and \
                            ly >= 0 and ly < dy and \
                            lx >= 0 and lx < dx:
                        if image[lz, ly, lx] >= image[z, y, x]:
                            out[z, y, x, 0] += powers[i]

                    # CORONAL
                    lx = x + positions[i][0]
                    ly = y
                    lz = z + positions[i][1]
                    if lz >= 0 and lz < dz and \
                            ly >= 0 and ly < dy and \
                            lx >= 0 and lx < dx:
                        if image[lz, ly, lx] >= image[z, y, x]:
                            out[z, y, x, 1] += powers[i]

                    #  # SAGITAL
                    lx = x
                    ly = y + positions[i][0]
                    lz = z + positions[i][1]
                    if lz >= 0 and lz < dz and \
                            ly >= 0 and ly < dy and \
                            lx >= 0 and lx < dx:
                        if image[lz, ly, lx] >= image[z, y, x]:
                            out[z, y, x, 2] += powers[i]


def cy_simple_lbp(image_t[:, :, :] image, np.uint8_t[:, :, :, :] out):
    return _cy_simple_lbp(image, out)


def simple_lbp(np.ndarray[image_t, ndim=3] image):
    cdef np.ndarray[np.uint8_t, ndim=4] out
    cdef dx, dy, dz
    dz = image.shape[0]
    dy = image.shape[1]
    dx = image.shape[2]
    out = np.zeros(shape=(dz, dy, dx, 3), dtype=np.uint8)
    cy_simple_lbp(image, out)
    return out


def test_2():
    cdef vector[bool] manolo
    manolo.push_back(True)
    manolo.push_back(False)
    manolo.push_back(False)
    manolo.push_back(True)

    return manolo
