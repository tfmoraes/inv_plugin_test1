#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import numpy as np
import wx

import schwarzp

def imgnormalize(data, srange=(0, 255)):
    """
    Normalize image pixel intensity for int16 gray scale values.

    :param data: image matrix
    :param srange: range for normalization, default is 0 to 255
    :return: normalized pixel intensity matrix
    """

    dataf = np.asarray(data)
    rangef = np.asarray(srange)
    faux = np.ravel(dataf).astype(float)
    minimum = np.min(faux)
    maximum = np.max(faux)
    lower = rangef[0]
    upper = rangef[1]

    if minimum == maximum:
        datan = np.ones(dataf.shape)*(upper + lower) / 2.
    else:
        datan = (faux-minimum)*(upper-lower) / (maximum-minimum) + lower

    datan = np.reshape(datan, dataf.shape)
    datan = datan.astype(np.int16)

    return datan


def np2bitmap(arr):
    try:
        height, width, bands = arr.shape
        npimg = arr
    except ValueError:
        height, width = arr.shape
        bands = 3
        arr = imgnormalize(arr, (0, 255))
        npimg = np.zeros((height, width, bands), dtype=np.uint8)
        npimg[:, :, 0] = arr
        npimg[:, :, 1] = arr
        npimg[:, :, 2] = arr

    image = wx.EmptyImage(width, height)
    image.SetData(npimg.tostring())
    return image.ConvertToBitmap()


class GUISchwarzP(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)

        self.np_img = None
        self._init_gui()
        self._bind_events()
        self.update_image()

    def _init_gui(self):
        init_from = "-10.0"
        init_to = "10.0"
        init_size = "250"

        # Dir X
        lbl_from_x = wx.StaticText(self, -1, "From:", style=wx.ALIGN_RIGHT)
        self.spin_from_x = wx.SpinCtrlDouble(
            self, -1, init_from, min=-1000.0, max=1000.0
        )
        lbl_to_x = wx.StaticText(self, -1, "To:", style=wx.ALIGN_RIGHT)
        self.spin_to_x = wx.SpinCtrlDouble(
            self, -1, init_to, min=-1000.0, max=1000.0
        )
        lbl_size_x = wx.StaticText(self, -1, "Size:", style=wx.ALIGN_RIGHT)
        self.spin_size_x = wx.SpinCtrl(
            self, -1, init_size, min=50, max=1000
        )

        # Dir Y
        lbl_from_y = wx.StaticText(self, -1, "From:", style=wx.ALIGN_RIGHT)
        self.spin_from_y = wx.SpinCtrlDouble(
            self, -1, init_from, min=-1000.0, max=1000.0
        )
        lbl_to_y = wx.StaticText(self, -1, "To:", style=wx.ALIGN_RIGHT)
        self.spin_to_y = wx.SpinCtrlDouble(
            self, -1, init_to, min=-1000.0, max=1000.0
        )
        lbl_size_y = wx.StaticText(self, -1, "Size:", style=wx.ALIGN_RIGHT)
        self.spin_size_y = wx.SpinCtrl(
            self, -1, init_size, min=50, max=1000
        )

        # Dir Z
        lbl_from_z = wx.StaticText(self, -1, "From:", style=wx.ALIGN_RIGHT)
        self.spin_from_z = wx.SpinCtrlDouble(
            self, -1, init_from, min=-1000.0, max=1000.0
        )
        lbl_to_z = wx.StaticText(self, -1, "To:", style=wx.ALIGN_RIGHT)
        self.spin_to_z = wx.SpinCtrlDouble(
            self, -1, init_to, min=-1000.0, max=1000.0
        )
        lbl_size_z = wx.StaticText(self, -1, "Size:", style=wx.ALIGN_RIGHT)
        self.spin_size_z = wx.SpinCtrl(
            self, -1, init_size, min=50, max=1000
        )

        self.image_panel = wx.Panel(self, -1)

        sizer_dirx = wx.StaticBoxSizer(
            wx.StaticBox(self, -1, "Direction X"), wx.VERTICAL
        )
        sizer_dirx.Add(lbl_from_x, 0, wx.LEFT, 5)
        sizer_dirx.Add(self.spin_from_x, 0, wx.ALL, 5)
        sizer_dirx.Add(lbl_to_x, 0, wx.LEFT, 5)
        sizer_dirx.Add(self.spin_to_x, 0, wx.ALL, 5)
        sizer_dirx.Add(lbl_size_x, 0, wx.LEFT, 5)
        sizer_dirx.Add(self.spin_size_x, 0, wx.ALL, 5)

        sizer_diry = wx.StaticBoxSizer(
            wx.StaticBox(self, -1, "Direction Y"), wx.VERTICAL
        )
        sizer_diry.Add(lbl_from_y, 0, wx.LEFT, 5)
        sizer_diry.Add(self.spin_from_y, 0, wx.ALL, 5)
        sizer_diry.Add(lbl_to_y, 0, wx.LEFT, 5)
        sizer_diry.Add(self.spin_to_y, 0, wx.ALL, 5)
        sizer_diry.Add(lbl_size_y, 0, wx.LEFT, 5)
        sizer_diry.Add(self.spin_size_y, 0, wx.ALL, 5)

        sizer_dirz = wx.StaticBoxSizer(
            wx.StaticBox(self, -1, "Direction Z"), wx.VERTICAL
        )
        sizer_dirz.Add(lbl_from_z, 0, wx.LEFT, 5)
        sizer_dirz.Add(self.spin_from_z, 0, wx.ALL, 5)
        sizer_dirz.Add(lbl_to_z, 0, wx.LEFT, 5)
        sizer_dirz.Add(self.spin_to_z, 0, wx.ALL, 5)
        sizer_dirz.Add(lbl_size_z, 0, wx.LEFT, 5)
        sizer_dirz.Add(self.spin_size_z, 0, wx.ALL, 5)

        sizer_dirs = wx.BoxSizer(wx.HORIZONTAL)
        sizer_dirs.Add(sizer_dirx, 0, wx.ALL, 5)
        sizer_dirs.Add(sizer_diry, 0, wx.ALL, 5)
        sizer_dirs.Add(sizer_dirz, 0, wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(sizer_dirs, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.image_panel, 2, wx.EXPAND | wx.ALL,  5)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        self.image_panel.Bind(wx.EVT_PAINT, self.OnPaint)

        self.spin_from_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_to_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_size_x.Bind(wx.EVT_SPINCTRL, self.OnSetValues)

        self.spin_from_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_to_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_size_y.Bind(wx.EVT_SPINCTRL, self.OnSetValues)

        self.spin_from_z.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_to_z.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_size_z.Bind(wx.EVT_SPINCTRL, self.OnSetValues)

    def update_image(self):
        init_x = self.spin_from_x.GetValue()
        end_x = self.spin_to_x.GetValue()
        size_x = self.spin_size_x.GetValue()

        init_y = self.spin_from_y.GetValue()
        end_y = self.spin_to_y.GetValue()
        size_y = self.spin_size_y.GetValue()

        init_z = self.spin_from_z.GetValue()
        end_z = self.spin_to_z.GetValue()
        size_z = self.spin_size_z.GetValue()

        self.np_img = schwarzp.create_schwarzp(init_x, end_x, init_y, end_y, 1.0, 1.0, size_x, size_y, 1)[0]

    def OnSetValues(self, evt):
        self.update_image()
        self.Refresh()

    def OnPaint(self, evt):
        if self.np_img is None:
            pass

        gc = wx.GraphicsContext.Create(self.image_panel)
        gc.DrawBitmap(np2bitmap(self.np_img), 0, 0, 256, 256)
        gc.Flush()



class MyApp(wx.App):
    def OnInit(self):
        self.GUISchwarzP = GUISchwarzP(None, -1, "")
        self.SetTopWindow(self.GUISchwarzP)
        self.GUISchwarzP.Show()
        return True



if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
