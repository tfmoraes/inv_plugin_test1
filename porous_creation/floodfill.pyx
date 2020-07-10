#cython: language_level=3str

import numpy as np
cimport numpy as np
cimport cython

from collections import deque

from cython.parallel import prange
from libc.math cimport floor, ceil
from libcpp cimport bool
from libcpp.deque cimport deque as cdeque
from libcpp.vector cimport vector

from cy_my_types cimport image_t, mask_t

cdef struct s_coord:
    int x
    int y
    int z
    int sx
    int sy
    int sz

ctypedef s_coord coord

@cython.boundscheck(False) # turn of bounds-checking for entire function
@cython.wraparound(False)
@cython.nonecheck(False)
def floodfill_voronoy(np.ndarray[np.float32_t, ndim=3] data, list seeds, np.ndarray[mask_t, ndim=3] strct):
    cdef int x, y, z, sx, sy, sz
    cdef int dx, dy, dz
    cdef int odx, ody, odz
    cdef int xo, yo, zo
    cdef int i, j, k
    cdef int offset_x, offset_y, offset_z
    cdef float dist

    dz = data.shape[0]
    dy = data.shape[1]
    dx = data.shape[2]

    odz = strct.shape[0]
    ody = strct.shape[1]
    odx = strct.shape[2]

    cdef cdeque[coord] stack
    cdef coord c

    offset_z = odz // 2
    offset_y = ody // 2
    offset_x = odx // 2

    for i, j, k in seeds:
        c.x = i
        c.y = j
        c.z = k
        c.sx = i
        c.sy = j
        c.sz = k

        stack.push_back(c)

    with nogil:
        while stack.size():
            c = stack.back()
            stack.pop_back()

            x = c.x
            y = c.y
            z = c.z
            sx = c.sx
            sy = c.sy
            sz = c.sz

            dist = ((x - sx)**2 + (y - sy)**2 + (z - sz)**2)**0.5
            if data[z, y, x] == -1 or dist < data[z, y, x]:
                data[z, y, x] = dist
                for k in xrange(odz):
                    zo = z + k - offset_z
                    for j in xrange(ody):
                        yo = y + j - offset_y
                        for i in xrange(odx):
                            xo = x + i - offset_x
                            if strct[k, j, i] and 0 <= xo < dx and 0 <= yo < dy and 0 <= zo < dz:
                                xo = x + i - offset_x
                                c.x = xo
                                c.y = yo
                                c.z = zo
                                c.sx = sx
                                c.sy = sy
                                c.sz = sz
                                stack.push_back(c)
