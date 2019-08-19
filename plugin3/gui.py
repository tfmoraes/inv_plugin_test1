import wx
from wx.lib.pubsub import pub as Publisher


class GUIIsotropic(wx.Dialog):
    def __init__(self, parent, title="Isotropic", style=wx.DEFAULT_DIALOG_STYLE|wx.FRAME_FLOAT_ON_PARENT|wx.STAY_ON_TOP):
        wx.Dialog.__init__(self, parent, -1, title=title, style=style)

        self.spacing_original_x = 1.0
        self.spacing_original_y = 1.0
        self.spacing_original_z = 1.0

        self.spacing_new_x = 1.0
        self.spacing_new_y = 1.0
        self.spacing_new_z = 1.0

        self._init_gui()

        self.set_original_spacing(
            self.spacing_original_x,
            self.spacing_original_y,
            self.spacing_original_z
        )

        self.set_new_spacing(
            self.spacing_new_x,
            self.spacing_new_y,
            self.spacing_new_z
        )

        self._bind_events()

    def set_original_spacing(self, sx, sy, sz):
        self.spacing_original_x = sx
        self.spacing_original_y = sy
        self.spacing_original_z = sz

        self.txt_spacing_original_x.ChangeValue(str(sx))
        self.txt_spacing_original_y.ChangeValue(str(sy))
        self.txt_spacing_original_z.ChangeValue(str(sz))

    def set_new_spacing(self, sx, sy, sz):
        self.spacing_new_x = sx
        self.spacing_new_y = sy
        self.spacing_new_z = sz

        self.txt_spacing_new_x.ChangeValue(str(sx))
        self.txt_spacing_new_y.ChangeValue(str(sy))
        self.txt_spacing_new_z.ChangeValue(str(sz))

    def _init_gui(self):
        self.txt_spacing_original_x = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
        self.txt_spacing_original_y = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
        self.txt_spacing_original_z = wx.TextCtrl(self, -1, style=wx.TE_READONLY)

        self.txt_spacing_new_x = wx.TextCtrl(self, -1)
        self.txt_spacing_new_y = wx.TextCtrl(self, -1, style=wx.TE_READONLY)
        self.txt_spacing_new_z = wx.TextCtrl(self, -1, style=wx.TE_READONLY)

        self.button_ok = wx.Button(self, wx.ID_OK)
        self.button_cancel = wx.Button(self, wx.ID_CANCEL)

        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(self.button_ok)
        button_sizer.AddButton(self.button_cancel)
        button_sizer.Realize()

        sizer_original = wx.StaticBoxSizer(wx.VERTICAL, self, label="Original spacing")
        sizer_original.Add(self.txt_spacing_original_x)
        sizer_original.Add(self.txt_spacing_original_y)
        sizer_original.Add(self.txt_spacing_original_z)

        sizer_new = wx.StaticBoxSizer(wx.VERTICAL, self, label="New spacing")
        sizer_new.Add(self.txt_spacing_new_x)
        sizer_new.Add(self.txt_spacing_new_y)
        sizer_new.Add(self.txt_spacing_new_z)

        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        content_sizer.Add(sizer_original)
        content_sizer.Add(sizer_new)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(content_sizer)
        main_sizer.Add(button_sizer)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        self.txt_spacing_new_x.Bind(wx.EVT_KILL_FOCUS, self.OnSetNewSpacing)
        self.button_ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)

    def OnSetNewSpacing(self, evt):
        if self.txt_spacing_new_x.GetValue():
            try:
                new_spacing_x = float(self.txt_spacing_new_x.GetValue())
            except ValueError:
                new_spacing_x = self.spacing_new_x
        else:
            new_spacing_x = self.txt_spacing_new_x.GetValue()

        self.set_new_spacing(new_spacing_x, new_spacing_x, new_spacing_x)

    def OnOk(self, evt):
        self.EndModal(wx.ID_OK)

    def OnCancel(self, evt):
        self.EndModal(wx.ID_CANCEL)
