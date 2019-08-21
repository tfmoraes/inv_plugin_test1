import vtk
import wx
from six import with_metaclass
from wx.lib.pubsub import pub as Publisher

import invesalius.constants as const
import invesalius.data.cursor_actors as ca
import invesalius.utils as utils
from invesalius.data import styles

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


class ClassificationStyle(styles.DefaultInteractorStyle):
    def __init__(self, viewer):
        styles.DefaultInteractorStyle.__init__(self, viewer)

        self.state_code = const.SLICE_STATE_WATERSHED

        self.viewer = viewer
        self.orientation = self.viewer.orientation
        self.matrix = None

        self.config = ClassificationConfig()

        self.picker = vtk.vtkWorldPointPicker()

        self.AddObserver("EnterEvent", self.OnEnterInteractor)
        self.AddObserver("LeaveEvent", self.OnLeaveInteractor)

        self.RemoveObservers("MouseWheelForwardEvent")
        self.RemoveObservers("MouseWheelBackwardEvent")
        self.AddObserver("MouseWheelForwardEvent", self.WOnScrollForward)
        self.AddObserver("MouseWheelBackwardEvent", self.WOnScrollBackward)

        self.AddObserver("LeftButtonPressEvent", self.OnBrushClick)
        self.AddObserver("LeftButtonReleaseEvent", self.OnBrushRelease)
        self.AddObserver("MouseMoveEvent", self.OnBrushMove)

        self._set_cursor()
        self.viewer.slice_data.cursor.Show(0)

    def SetUp(self):
        mask = self.viewer.slice_.current_mask.matrix
        self._create_mask()
        self.viewer.slice_.to_show_aux = "classify"
        self.viewer.slice_.aux_matrices_colours[self.viewer.slice_.to_show_aux] = {
            0: (0.0, 0.0, 0.0, 0.0),
            1: (0.0, 1.0, 0.0, 1.0),
            2: (1.0, 0.0, 0.0, 1.0),
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
        Publisher.unsubscribe(
            self.expand_watershed, "Expand watershed to 3D " + self.orientation
        )
        Publisher.unsubscribe(self.set_bformat, "Set watershed brush format")
        Publisher.unsubscribe(self.set_bsize, "Set watershed brush size")
        self.RemoveAllObservers()
        self.viewer.slice_.to_show_aux = ""
        self.viewer.OnScrollBar()

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

    def _set_cursor(self):
        if self.config.cursor_type == const.BRUSH_SQUARE:
            cursor = ca.CursorRectangle()
        elif self.config.cursor_type == const.BRUSH_CIRCLE:
            cursor = ca.CursorCircle()

        cursor.SetOrientation(self.orientation)
        n = self.viewer.slice_data.number
        coordinates = {"SAGITAL": [n, 0, 0], "CORONAL": [0, n, 0], "AXIAL": [0, 0, n]}
        cursor.SetPosition(coordinates[self.orientation])
        spacing = self.viewer.slice_.spacing
        cursor.SetSpacing(spacing)
        cursor.SetColour(self.viewer._brush_cursor_colour)
        cursor.SetSize(self.config.cursor_size)
        self.viewer.slice_data.SetCursor(cursor)

    def set_bsize(self, size):
        self.config.cursor_size = size
        self.viewer.slice_data.cursor.SetSize(size)

    def set_bformat(self, brush_format):
        self.config.cursor_type = brush_format
        self._set_cursor()

    def OnEnterInteractor(self, obj, evt):
        if self.viewer.slice_.buffer_slices[self.orientation].mask is None:
            return
        self.viewer.slice_data.cursor.Show()
        self.viewer.interactor.SetCursor(wx.Cursor(wx.CURSOR_BLANK))
        self.viewer.interactor.Render()

    def OnLeaveInteractor(self, obj, evt):
        self.viewer.slice_data.cursor.Show(0)
        self.viewer.interactor.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        self.viewer.interactor.Render()

    def WOnScrollBackward(self, obj, evt):
        iren = self.viewer.interactor
        viewer = self.viewer
        if iren.GetControlKey():
            mouse_x, mouse_y = iren.GetEventPosition()
            render = iren.FindPokedRenderer(mouse_x, mouse_y)
            slice_data = self.viewer.get_slice_data(render)
            cursor = slice_data.cursor
            size = cursor.radius * 2
            size -= 1

            if size > 0:
                Publisher.sendMessage("Set watershed brush size", size=size)
                cursor.SetPosition(cursor.position)
                self.viewer.interactor.Render()
        else:
            self.OnScrollBackward(obj, evt)

    def WOnScrollForward(self, obj, evt):
        iren = self.viewer.interactor
        viewer = self.viewer
        if iren.GetControlKey():
            mouse_x, mouse_y = iren.GetEventPosition()
            render = iren.FindPokedRenderer(mouse_x, mouse_y)
            slice_data = self.viewer.get_slice_data(render)
            cursor = slice_data.cursor
            size = cursor.radius * 2
            size += 1

            if size <= 100:
                Publisher.sendMessage("Set watershed brush size", size=size)
                cursor.SetPosition(cursor.position)
                self.viewer.interactor.Render()
        else:
            self.OnScrollForward(obj, evt)

    def OnBrushClick(self, obj, evt):
        if self.viewer.slice_.buffer_slices[self.orientation].mask is None:
            return

        print("OnClick")

        viewer = self.viewer
        iren = viewer.interactor

        viewer._set_editor_cursor_visibility(1)

        mouse_x, mouse_y = iren.GetEventPosition()
        render = iren.FindPokedRenderer(mouse_x, mouse_y)
        slice_data = viewer.get_slice_data(render)

        coord = self.viewer.get_coordinate_cursor(mouse_x, mouse_y, picker=None)
        position = self.viewer.get_slice_pixel_coord_by_screen_pos(
            mouse_x, mouse_y, self.picker
        )

        slice_data.cursor.Show()
        slice_data.cursor.SetPosition(coord)

        cursor = slice_data.cursor
        radius = cursor.radius

        operation = self.config.operation

        if operation == BRUSH_FOREGROUND:
            if iren.GetControlKey():
                operation = BRUSH_BACKGROUND
            elif iren.GetShiftKey():
                operation = BRUSH_ERASE
        elif operation == BRUSH_BACKGROUND:
            if iren.GetControlKey():
                operation = BRUSH_FOREGROUND
            elif iren.GetShiftKey():
                operation = BRUSH_ERASE

        n = self.viewer.slice_data.number
        self.edit_mask_pixel(
            operation, n, cursor.GetPixels(), position, radius, self.orientation
        )
        if self.orientation == "AXIAL":
            mask = self.matrix[n, :, :]
        elif self.orientation == "CORONAL":
            mask = self.matrix[:, n, :]
        elif self.orientation == "SAGITAL":
            mask = self.matrix[:, :, n]
        # TODO: To create a new function to reload images to viewer.
        viewer.OnScrollBar()

    def OnBrushMove(self, obj, evt):
        if self.viewer.slice_.buffer_slices[self.orientation].mask is None:
            return

        print("OnMove")

        viewer = self.viewer
        iren = viewer.interactor

        viewer._set_editor_cursor_visibility(1)

        mouse_x, mouse_y = iren.GetEventPosition()
        render = iren.FindPokedRenderer(mouse_x, mouse_y)
        slice_data = viewer.get_slice_data(render)

        coord = self.viewer.get_coordinate_cursor(mouse_x, mouse_y, self.picker)
        slice_data.cursor.SetPosition(coord)

        if self.left_pressed:
            cursor = slice_data.cursor
            position = self.viewer.get_slice_pixel_coord_by_world_pos(*coord)
            radius = cursor.radius

            if isinstance(position, int) and position < 0:
                position = viewer.calculate_matrix_position(coord)

            operation = self.config.operation

            if operation == BRUSH_FOREGROUND:
                if iren.GetControlKey():
                    operation = BRUSH_BACKGROUND
                elif iren.GetShiftKey():
                    operation = BRUSH_ERASE
            elif operation == BRUSH_BACKGROUND:
                if iren.GetControlKey():
                    operation = BRUSH_FOREGROUND
                elif iren.GetShiftKey():
                    operation = BRUSH_ERASE

            n = self.viewer.slice_data.number
            self.edit_mask_pixel(
                operation, n, cursor.GetPixels(), position, radius, self.orientation
            )
            if self.orientation == "AXIAL":
                mask = self.matrix[n, :, :]
            elif self.orientation == "CORONAL":
                mask = self.matrix[:, n, :]
            elif self.orientation == "SAGITAL":
                mask = self.matrix[:, :, n]
            # TODO: To create a new function to reload images to viewer.
            viewer.OnScrollBar(update3D=False)

        else:
            viewer.interactor.Render()

    def OnBrushRelease(self, evt, obj):
        n = self.viewer.slice_data.number
        self.viewer.slice_.discard_all_buffers()
        if self.orientation == "AXIAL":
            image = self.viewer.slice_.matrix[n]
            mask = self.viewer.slice_.current_mask.matrix[n + 1, 1:, 1:]
            self.viewer.slice_.current_mask.matrix[n + 1, 0, 0] = 1
            markers = self.matrix[n]

        elif self.orientation == "CORONAL":
            image = self.viewer.slice_.matrix[:, n, :]
            mask = self.viewer.slice_.current_mask.matrix[1:, n + 1, 1:]
            self.viewer.slice_.current_mask.matrix[0, n + 1, 0]
            markers = self.matrix[:, n, :]

        elif self.orientation == "SAGITAL":
            image = self.viewer.slice_.matrix[:, :, n]
            mask = self.viewer.slice_.current_mask.matrix[1:, 1:, n + 1]
            self.viewer.slice_.current_mask.matrix[0, 0, n + 1]
            markers = self.matrix[:, :, n]

        ww = self.viewer.slice_.window_width
        wl = self.viewer.slice_.window_level

        if BRUSH_BACKGROUND in markers and BRUSH_FOREGROUND in markers:
            # w_algorithm = WALGORITHM[self.config.algorithm]
            bstruct = generate_binary_structure(2, CON2D[self.config.con_2d])
            if self.config.use_ww_wl:
                if self.config.algorithm == "Watershed":
                    tmp_image = ndimage.morphological_gradient(
                        get_LUT_value(image, ww, wl).astype("uint16"),
                        self.config.mg_size,
                    )
                    tmp_mask = watershed(tmp_image, markers.astype("int16"), bstruct)
                else:
                    # tmp_image = ndimage.gaussian_filter(get_LUT_value(image, ww, wl).astype('uint16'), self.config.mg_size)
                    # tmp_image = ndimage.morphological_gradient(
                    # get_LUT_value(image, ww, wl).astype('uint16'),
                    # self.config.mg_size)
                    tmp_image = get_LUT_value(image, ww, wl).astype("uint16")
                    # markers[markers == 2] = -1
                    tmp_mask = watershed_ift(
                        tmp_image, markers.astype("int16"), bstruct
                    )
                    # markers[markers == -1] = 2
                    # tmp_mask[tmp_mask == -1]  = 2

            else:
                if self.config.algorithm == "Watershed":
                    tmp_image = ndimage.morphological_gradient(
                        (image - image.min()).astype("uint16"), self.config.mg_size
                    )
                    tmp_mask = watershed(tmp_image, markers.astype("int16"), bstruct)
                else:
                    # tmp_image = (image - image.min()).astype('uint16')
                    # tmp_image = ndimage.gaussian_filter(tmp_image, self.config.mg_size)
                    # tmp_image = ndimage.morphological_gradient((image - image.min()).astype('uint16'), self.config.mg_size)
                    tmp_image = image - image.min().astype("uint16")
                    tmp_mask = watershed_ift(
                        tmp_image, markers.astype("int16"), bstruct
                    )

            if self.viewer.overwrite_mask:
                mask[:] = 0
                mask[tmp_mask == 1] = 253
            else:
                mask[(tmp_mask == 2) & ((mask == 0) | (mask == 2) | (mask == 253))] = 2
                mask[
                    (tmp_mask == 1) & ((mask == 0) | (mask == 2) | (mask == 253))
                ] = 253

            self.viewer.slice_.current_mask.was_edited = True
            self.viewer.slice_.current_mask.clear_history()

            # Marking the project as changed
            session = ses.Session()
            session.ChangeProject()

        Publisher.sendMessage("Reload actual slice")

    def edit_mask_pixel(self, operation, n, index, position, radius, orientation):
        if orientation == "AXIAL":
            mask = self.matrix[n, :, :]
        elif orientation == "CORONAL":
            mask = self.matrix[:, n, :]
        elif orientation == "SAGITAL":
            mask = self.matrix[:, :, n]

        spacing = self.viewer.slice_.spacing
        if hasattr(position, "__iter__"):
            px, py = position
            if orientation == "AXIAL":
                sx = spacing[0]
                sy = spacing[1]
            elif orientation == "CORONAL":
                sx = spacing[0]
                sy = spacing[2]
            elif orientation == "SAGITAL":
                sx = spacing[2]
                sy = spacing[1]

        else:
            if orientation == "AXIAL":
                sx = spacing[0]
                sy = spacing[1]
                py = position / mask.shape[1]
                px = position % mask.shape[1]
            elif orientation == "CORONAL":
                sx = spacing[0]
                sy = spacing[2]
                py = position / mask.shape[1]
                px = position % mask.shape[1]
            elif orientation == "SAGITAL":
                sx = spacing[2]
                sy = spacing[1]
                py = position / mask.shape[1]
                px = position % mask.shape[1]

        cx = index.shape[1] / 2 + 1
        cy = index.shape[0] / 2 + 1
        xi = int(px - index.shape[1] + cx)
        xf = int(xi + index.shape[1])
        yi = int(py - index.shape[0] + cy)
        yf = int(yi + index.shape[0])

        if yi < 0:
            index = index[abs(yi) :, :]
            yi = 0
        if yf > mask.shape[0]:
            index = index[: index.shape[0] - (yf - mask.shape[0]), :]
            yf = mask.shape[0]

        if xi < 0:
            index = index[:, abs(xi) :]
            xi = 0
        if xf > mask.shape[1]:
            index = index[:, : index.shape[1] - (xf - mask.shape[1])]
            xf = mask.shape[1]

        # Verifying if the points is over the image array.
        if (not 0 <= xi <= mask.shape[1] and not 0 <= xf <= mask.shape[1]) or (
            not 0 <= yi <= mask.shape[0] and not 0 <= yf <= mask.shape[0]
        ):
            return

        roi_m = mask[yi:yf, xi:xf]

        # Checking if roi_i has at least one element.
        if roi_m.size:
            roi_m[index] = operation

    def expand_watershed(self):
        # mask[:] = tmp_mask
        self.viewer.slice_.current_mask.matrix[0] = 1
        self.viewer.slice_.current_mask.matrix[:, 0, :] = 1
        self.viewer.slice_.current_mask.matrix[:, :, 0] = 1

        self.viewer.slice_.discard_all_buffers()
        self.viewer.slice_.current_mask.clear_history()
        Publisher.sendMessage("Reload actual slice")

        # Marking the project as changed
        session = ses.Session()
        session.ChangeProject()
