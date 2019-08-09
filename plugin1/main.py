from wx.lib.pubsub import pub as Publisher
import vtk

from invesalius.data import styles

from . import utils


class ManoloStyle(styles.DefaultInteractorStyle):
    def __init__(self, viewer):
        styles.DefaultInteractorStyle.__init__(self, viewer)

        self.viewer = viewer
        self.orientation = self.viewer.orientation
        self.picker = vtk.vtkWorldPointPicker()

    def SetUp(self):
        self.AddObserver("LeftButtonPressEvent", self.OnManoloClick)
        self.AddObserver("LeftButtonReleaseEvent", self.OnManoloRelease)
        self.AddObserver("MouseMoveEvent", self.OnManoloMove)

    def CleanUp(self):
        print("Cleaning Up")

    def OnManoloClick(self, evt, obj):
        print("ManoloClick")

    def OnManoloRelease(self, evt, obj):
        print("ManoloRelease")

    def OnManoloMove(self, evt, obj):
        if self.left_pressed:
            if (self.viewer.slice_.buffer_slices[self.orientation].mask is None):
                return

            viewer = self.viewer
            iren = viewer.interactor
            mouse_x, mouse_y = iren.GetEventPosition()
            x, y, z = self.viewer.get_voxel_coord_by_screen_pos(mouse_x, mouse_y, self.picker)

            print(f"Click in position: {x}, {y}, {z}")
            mask = self.viewer.get_actual_mask()
            mask_matrix = mask.matrix[1:, 1:, 1:]
            mask_matrix[z, y, x] = 254

            self.viewer.discard_mask_cache(all_orientations=True)

            mask.was_edited = True
            Publisher.sendMessage('Reload actual slice')


def load():
    print("Loading plugin")
    utils.hello("manolo")
    style_id = styles.Styles.add_style(ManoloStyle, 2)
    print(f"Style: {style_id}")
    Publisher.sendMessage("Disable actual style")
    Publisher.sendMessage("Enable style", style=style_id)
