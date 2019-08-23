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
        self.clf = DecisionTreeClassifier(max_depth=5)


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

    def SetUp(self):
        self._create_mask()
        self.viewer.slice_.to_show_aux = "classify"
        self.viewer.slice_.aux_matrices_colours[self.viewer.slice_.to_show_aux] = {
            BRUSH_ERASE: (0.0, 0.0, 0.0, 0.0),
            BRUSH_FOREGROUND: (0.0, 1.0, 0.0, 1.0),
            BRUSH_BACKGROUND: (1.0, 0.0, 0.0, 1.0),
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
        if iren.GetControlKey():
            self.fill_value = BRUSH_BACKGROUND
        elif iren.GetShiftKey():
            self.fill_value = BRUSH_ERASE
        else:
            self.fill_value = BRUSH_FOREGROUND

    def before_brush_move(self):
        iren = self.viewer.interactor
        if iren.GetControlKey():
            self.fill_value = BRUSH_BACKGROUND
        elif iren.GetShiftKey():
            self.fill_value = BRUSH_ERASE
        else:
            self.fill_value = BRUSH_FOREGROUND

    def after_brush_release(self):
        if BRUSH_FOREGROUND in self.matrix and BRUSH_BACKGROUND in self.matrix:
            image = self.viewer.slice_.matrix
            values_marker1 = image[self.matrix == BRUSH_FOREGROUND]
            values_marker2 = image[self.matrix == BRUSH_BACKGROUND]
            clf_values = np.empty(values_marker1.shape[0] + values_marker2.shape[0])
            clf_values[:values_marker1.shape[0]] = BRUSH_FOREGROUND
            clf_values[values_marker1.shape[0]:] = BRUSH_BACKGROUND
            values_markers = np.append(values_marker1, values_marker2)
            print(clf_values.shape, values_markers.shape)
            mask = self.viewer.slice_.current_mask.matrix[1:, 1:, 1:]
            clf = DecisionTreeClassifier(max_depth=5)
            clf.fit(values_markers.reshape(-1, 1), clf_values)
            Z = clf.predict(image.flatten().reshape(-1, 1))
            Z.shape = image.shape
            mask[Z == BRUSH_FOREGROUND] = 254
