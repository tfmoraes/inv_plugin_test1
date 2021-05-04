import os
import tempfile

import wx

#  from invesalius import project
from pubsub import pub as Publisher


class Window(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title="Remove non-visible faces",
            style=wx.DEFAULT_DIALOG_STYLE | wx.FRAME_FLOAT_ON_PARENT,
        )

        self._init_gui()
        self._bind_events()

    def _init_gui(self):
        choices = ["Camboja", "Manolo"]
        self.surfaces_combo = wx.ComboBox(self, -1, choices=choices, value=choices[0])
        self.overwrite_check = wx.CheckBox(self, -1, "Overwrite surface")
        self.remove_visible_check = wx.CheckBox(self, -1, "Remove visible faces")
        apply_button = wx.Button(self, wx.ID_APPLY, "Apply")
        close_button = wx.Button(self, wx.ID_CLOSE, "Close")

        combo_sizer = wx.BoxSizer(wx.HORIZONTAL)
        combo_sizer.Add(
            wx.StaticText(self, -1, "Surface"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT,
            5,
        )
        combo_sizer.Add(self.surfaces_combo, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(apply_button)
        button_sizer.AddButton(close_button)
        button_sizer.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(combo_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.overwrite_check, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.remove_visible_check, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizerAndFit(sizer)

    def _bind_events(self):
        self.Bind(wx.EVT_BUTTON, self.on_apply, id=wx.ID_APPLY)
        self.Bind(wx.EVT_BUTTON, self.on_quit, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_CLOSE, self.on_quit)

    def on_quit(self, evt):
        print("closing")
        self.Destroy()

    def on_apply(self, evt):
        surface = self.surfaces_combo.GetValue()
        print("applying", surface)


if __name__ == "__main__":
    app = wx.App()
    window = Window(None)
    window.Show()
    app.MainLoop()
