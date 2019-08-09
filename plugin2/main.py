import numpy as np
from wx.lib.pubsub import pub as Publisher

from invesalius.data import imagedata_utils


def create_schwarzp(sx=256, sy=256, sz=256):
    init = -10 / 2.0 * np.pi 
    end =  10 / 2.0 * np.pi 
    z, y, x = np.ogrid[
        init : end : complex(0, sz), init : end : complex(0, sy), init : end : complex(0, sx)
    ]
    return np.cos(x) + np.cos(y) + np.cos(z)


def load():
    schwarp_f = create_schwarzp()
    schwarp_i16 = imagedata_utils.imgnormalize(schwarp_f, (-1000, 1000))
    Publisher.sendMessage(
        "Create project from matrix", name="SchwarzP", matrix=schwarp_i16
    )
