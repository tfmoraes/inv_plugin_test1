from wx.lib.pubsub import pub as Publisher
import vtk

from invesalius.data import styles

from . import utils
from . import classifcation_style


def load():
    print("Loading plugin")
    utils.hello("manolo")
    style_id = styles.Styles.add_style(classifcation_style.ClassificationStyle, 2)
    print(f"Style: {style_id}")
    Publisher.sendMessage("Disable actual style")
    Publisher.sendMessage("Enable style", style=style_id)
