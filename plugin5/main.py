from pubsub import pub as Publisher
import vtk

from skimage.segmentation import felzenszwalb, slic, quickshift, watershed
from skimage.segmentation import mark_boundaries, find_boundaries
from skimage.util import img_as_float

from invesalius.data import styles


from invesalius.data import imagedata_utils as iu
from invesalius.data import slice_

def preprocess_image(image, window, level):
    image = iu.get_LUT_value_255(image, window, level)
    return img_as_float(image)


def load():
    print("Loading plugin")
    slc = slice_.Slice()
    image = slc.matrix
    window = slc.window_width
    level = slc.window_level
    image = preprocess_image(image, window, level)
    mask = slc.create_new_mask()
    mask.was_edited = True
    mask.matrix[0, :, :] = 1
    mask.matrix[:, 0, :] = 1
    mask.matrix[:, :, 0] = 1
    for i in range(image.shape[0]):
        mask.matrix[i+1, 1:, 1:] = find_boundaries(felzenszwalb(image[i])) * 255
