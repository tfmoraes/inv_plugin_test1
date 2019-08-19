import scipy.ndimage as nd
from wx.lib.pubsub import pub as Publisher

import invesalius.data.slice_ as slc


def make_orthogonal():
    s = slc.Slice()
    image_matrix = s.matrix
    spacing = s.spacing
    min_spacing = min(spacing)
    new_spacing = (min_spacing, min_spacing, min_spacing)
    zooms = [i / j for (i, j) in zip(spacing, new_spacing)]
    new_image = nd.zoom(
        image_matrix,
        zooms[::-1],
        output=image_matrix.dtype,
        mode="constant",
        cval=image_matrix.min(),
    )
    return new_image, new_spacing


def load():
    print("Loading plugin")
    new_image, new_spacing = make_orthogonal()
    Publisher.sendMessage(
        "Create project from matrix", name="Test", matrix=new_image, spacing=new_spacing
    )
