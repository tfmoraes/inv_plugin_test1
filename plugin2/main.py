from wx.lib.pubsub import pub as Publisher

from invesalius.data import imagedata_utils

from . import schwarp



def load():
    schwarp_f = schwarp.create_schwarzp()
    schwarp_i16 = imagedata_utils.imgnormalize(schwarp_f, (-1000, 1000))
    Publisher.sendMessage(
        "Create project from matrix", name="SchwarzP", matrix=schwarp_i16
    )
