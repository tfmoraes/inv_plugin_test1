import vtk
import wx
import numpy as np
from six import with_metaclass
from wx.lib.pubsub import pub as Publisher

import invesalius.constants as const
import invesalius.data.cursor_actors as ca
import invesalius.utils as utils
from invesalius.data import styles
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from scipy.ndimage import generate_binary_structure, gaussian_filter

import imageio

from . import simple_lbp
from . import floodfill

BRUSH_FOREGROUND = 1
BRUSH_BACKGROUND = 2
BRUSH_ERASE = 0

CON2D = {4: 1, 8: 2}
CON3D = {6: 1, 18: 2, 26: 3}

WATERSHED_OPERATIONS = {
    _("Erase"): BRUSH_ERASE,
    _("Foreground"): BRUSH_FOREGROUND,
    _("Background"): BRUSH_BACKGROUND,
}


class ClassificationConfig(with_metaclass(utils.Singleton, object)):
    def __init__(self):
        self.algorithm = "Watershed"
        self.con_2d = 4
        self.con_3d = 6
        self.mg_size = 3
        self.use_ww_wl = True
        self.operation = BRUSH_FOREGROUND
        self.cursor_type = const.BRUSH_CIRCLE
        self.cursor_size = const.BRUSH_SIZE

        Publisher.subscribe(self.set_operation, "Set watershed operation")
        Publisher.subscribe(self.set_use_ww_wl, "Set use ww wl")

        Publisher.subscribe(self.set_algorithm, "Set watershed algorithm")
        Publisher.subscribe(self.set_2dcon, "Set watershed 2d con")
        Publisher.subscribe(self.set_3dcon, "Set watershed 3d con")
        Publisher.subscribe(self.set_gaussian_size, "Set watershed gaussian size")

    def set_operation(self, operation):
        self.operation = WATERSHED_OPERATIONS[operation]

    def set_use_ww_wl(self, use_ww_wl):
        self.use_ww_wl = use_ww_wl

    def set_algorithm(self, algorithm):
        self.algorithm = algorithm

    def set_2dcon(self, con_2d):
        self.con_2d = con_2d

    def set_3dcon(self, con_3d):
        self.con_3d = con_3d

    def set_gaussian_size(self, size):
        self.mg_size = size


class Classifier(with_metaclass(utils.Singleton, object)):
    def __init__(self):
        self.clf = RandomForestClassifier()
        self.image = None
        self.lbp_image = None
        self.gx = None
        self.gy = None
        self.gz = None
        self.gm = None


class ClassificationStyle(styles.BaseImageEditionInteractorStyle):
    def __init__(self, viewer):
        super().__init__(viewer)
        self.state_code = const.SLICE_STATE_WATERSHED
        self.viewer = viewer
        self.orientation = self.viewer.orientation
        self.matrix = None
        self.fill_value = BRUSH_FOREGROUND
        self.config = ClassificationConfig()
        self.classifier = Classifier()

        if self.classifier.image is None:
            image = gaussian_filter(self.viewer.slice_.matrix, 1.5)
            #  gz, gy, gx = np.gradient(image)
            #  gm = np.sqrt(gx**2 + gy**2 + gz**2)
            #  self.classifier.gx = np.nan_to_num(gx / gm)
            #  self.classifier.gy = np.nan_to_num(gy / gm)
            #  self.classifier.gz = np.nan_to_num(gz / gm)
            #  self.classifier.gm = gm
            self.classifier.image = image
            self.classifier.lbp_image = simple_lbp.simple_lbp(image)

            imageio.imsave(
                "/tmp/saida.png", self.classifier.lbp_image[image.shape[0] // 2]
            )

    def SetUp(self):
        self._create_mask()
        self.viewer.slice_.to_show_aux = "classify"
        self.viewer.slice_.aux_matrices_colours[self.viewer.slice_.to_show_aux] = {
            BRUSH_ERASE: (0.0, 0.0, 0.0, 0.0),
            BRUSH_FOREGROUND: (0.0, 1.0, 0.0, 1.0),
        }
        self.viewer.OnScrollBar()

        x, y = self.viewer.interactor.ScreenToClient(wx.GetMousePosition())
        if self.viewer.interactor.HitTest((x, y)) == wx.HT_WINDOW_INSIDE:
            self.viewer.slice_data.cursor.Show()

            y = self.viewer.interactor.GetSize()[1] - y
            w_x, w_y, w_z = self.viewer.get_coordinate_cursor(x, y, self.picker)
            self.viewer.slice_data.cursor.SetPosition((w_x, w_y, w_z))

            self.viewer.interactor.SetCursor(wx.Cursor(wx.CURSOR_BLANK))
            self.viewer.interactor.Render()

    def CleanUp(self):
        # self._remove_mask()
        #  Publisher.unsubscribe(
        #  self.expand_watershed, "Expand watershed to 3D " + self.orientation
        #  )
        #  Publisher.unsubscribe(self.set_bformat, "Set watershed brush format")
        #  Publisher.unsubscribe(self.set_bsize, "Set watershed brush size")
        #  self.RemoveAllObservers()
        #  self.viewer.slice_.to_show_aux = ""
        #  self.viewer.OnScrollBar()

        self.viewer.slice_data.cursor.Show(0)
        self.viewer.interactor.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        self.viewer.interactor.Render()

    def _create_mask(self):
        if self.matrix is None:
            try:
                self.matrix = self.viewer.slice_.aux_matrices["classify"]
            except KeyError:
                self.temp_file, self.matrix = self.viewer.slice_.create_temp_mask()
                self.viewer.slice_.aux_matrices["classify"] = self.matrix

    def _remove_mask(self):
        if self.matrix is not None:
            self.matrix = None
            os.remove(self.temp_file)
            print("deleting", self.temp_file)

    def before_brush_click(self):
        iren = self.viewer.interactor
        if iren.GetShiftKey():
            self.fill_value = BRUSH_ERASE
        else:
            self.fill_value = BRUSH_FOREGROUND

    def before_brush_move(self):
        iren = self.viewer.interactor
        if iren.GetShiftKey():
            self.fill_value = BRUSH_ERASE
        else:
            self.fill_value = BRUSH_FOREGROUND

    def after_brush_release(self):
        n = self.viewer.slice_data.number
        lbp_image = self.classifier.lbp_image
        mask = self.matrix
        marked_values = lbp_image[mask == BRUSH_FOREGROUND]
        mean_lbp = marked_values.mean(0, dtype=np.float32)
        dists = np.linalg.norm(marked_values - mean_lbp, axis=1)
        std_dist = dists.mean()
        strct = np.array(generate_binary_structure(3, 1), dtype=np.uint8)
        print(mean_lbp, std_dist)
        print("BEFORE MARKED", (mask == BRUSH_FOREGROUND).sum())
        out = floodfill.texture_floodfill(
            lbp_image, mask, mean_lbp, BRUSH_FOREGROUND, std_dist, strct
        )
        print("AFTER MARKED", (out == BRUSH_FOREGROUND).sum())
        image_mask = self.viewer.slice_.current_mask.matrix
        image_mask[1:, 1:, 1:] = out * 255
        image_mask[0] = 255
        image_mask[:, 0, :] = 255
        image_mask[:, :, 0] = 255

        self.viewer.slice_.buffer_slices["AXIAL"].discard_mask()
        self.viewer.slice_.buffer_slices["CORONAL"].discard_mask()
        self.viewer.slice_.buffer_slices["SAGITAL"].discard_mask()

        self.viewer.slice_.buffer_slices["AXIAL"].discard_vtk_mask()
        self.viewer.slice_.buffer_slices["CORONAL"].discard_vtk_mask()
        self.viewer.slice_.buffer_slices["SAGITAL"].discard_vtk_mask()

        self.viewer.slice_.current_mask.was_edited = True
        Publisher.sendMessage("Reload actual slice")
