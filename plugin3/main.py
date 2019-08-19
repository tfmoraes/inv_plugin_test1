import scipy.ndimage as nd
import wx
from wx.lib.pubsub import pub as Publisher

import invesalius.data.slice_ as slc

from . import gui


def make_orthogonal(matrix, old_spacing, new_spacing):
    zooms = [i / j for (i, j) in zip(old_spacing, new_spacing)]
    new_image = nd.zoom(
        matrix,
        zooms[::-1],
        output=matrix.dtype,
        mode="constant",
        cval=matrix.min(),
    )
    print(f"Spacing: {old_spacing} -> {new_spacing}")
    print(f"Shape: {matrix.shape} -> {new_image.shape}")
    return new_image


def load():
    s = slc.Slice()

    image_matrix = s.matrix
    spacing = s.spacing
    min_spacing = min(spacing)
    new_spacing = (min_spacing, min_spacing, min_spacing)

    g = gui.GUIIsotropic(wx.GetApp().GetTopWindow())
    g.set_original_spacing(*spacing)
    g.set_new_spacing(*new_spacing)
    if g.ShowModal() == wx.ID_OK:
        new_spacing = (g.spacing_new_x, g.spacing_new_y, g.spacing_new_z)
        new_image = make_orthogonal(image_matrix, spacing, new_spacing)

        Publisher.sendMessage(
            "Create project from matrix", name="Test", matrix=new_image, spacing=new_spacing
        )
