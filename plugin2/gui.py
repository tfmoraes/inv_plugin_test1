#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import numpy as np
import wx
from wx.lib.pubsub import pub as Publisher

from invesalius.data import imagedata_utils

from . import schwarzp


def np2bitmap(arr):
    try:
        height, width, bands = arr.shape
        npimg = arr
    except ValueError:
        height, width = arr.shape
        bands = 3
        arr = imagedata_utils.imgnormalize(arr, (0, 255))
        npimg = np.zeros((height, width, bands), dtype=np.uint8)
        npimg[:, :, 0] = arr
        npimg[:, :, 1] = arr
        npimg[:, :, 2] = arr

    image = wx.Image(width, height)
    image.SetData(npimg.tostring())
    return image.ConvertToBitmap()


class GUISchwarzP(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, title="Schwarz-P creation", style=wx.MINIMIZE_BOX | wx.CLOSE_BOX)

        self.np_img = None
        self._init_gui()
        self._bind_events()
        self.update_image()

    def _init_gui(self):
        init_from = "-10.0"
        init_to = "10.0"
        init_size = "250"

        options = [
            "Schwarz P",
            "Schwarz D",
            "Gyroid",
            'Neovius',
            'iWP',
            'P_W_Hybrid',
            "Blobs",
        ]
        self.cb_option = wx.ComboBox(self, -1, options[0], choices=options, style=wx.CB_READONLY)

        # Dir X
        lbl_from_x = wx.StaticText(self, -1, "From:", style=wx.ALIGN_RIGHT)
        self.spin_from_x = wx.SpinCtrlDouble(
            self, -1, value=init_from, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_to_x = wx.StaticText(self, -1, "To:", style=wx.ALIGN_RIGHT)
        self.spin_to_x = wx.SpinCtrlDouble(
            self, -1, value=init_to, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_size_x = wx.StaticText(self, -1, "Size:", style=wx.ALIGN_RIGHT)
        self.spin_size_x = wx.SpinCtrl(
            self, -1, value=init_size, min=50, max=1000
        )

        # Dir Y
        lbl_from_y = wx.StaticText(self, -1, "From:", style=wx.ALIGN_RIGHT)
        self.spin_from_y = wx.SpinCtrlDouble(
            self, -1, value=init_from, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_to_y = wx.StaticText(self, -1, "To:", style=wx.ALIGN_RIGHT)
        self.spin_to_y = wx.SpinCtrlDouble(
            self, -1, value=init_to, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_size_y = wx.StaticText(self, -1, "Size:", style=wx.ALIGN_RIGHT)
        self.spin_size_y = wx.SpinCtrl(
            self, -1, value=init_size, min=50, max=1000
        )

        # Dir Z
        lbl_from_z = wx.StaticText(self, -1, "From:", style=wx.ALIGN_RIGHT)
        self.spin_from_z = wx.SpinCtrlDouble(
            self, -1, value=init_from, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_to_z = wx.StaticText(self, -1, "To:", style=wx.ALIGN_RIGHT)
        self.spin_to_z = wx.SpinCtrlDouble(
            self, -1, value=init_to, min=-1000.0, max=1000.0, inc=0.1
        )
        lbl_size_z = wx.StaticText(self, -1, "Size:", style=wx.ALIGN_RIGHT)
        self.spin_size_z = wx.SpinCtrl(
            self, -1, value=init_size, min=50, max=1000
        )


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

        self.image_panel = wx.Panel(self, -1)
        self.image_panel.SetMinSize(sizer_dirz.CalcMin())

        self.button_ok = wx.Button(self, wx.ID_OK)
        self.button_cancel = wx.Button(self, wx.ID_CANCEL)

        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(self.button_ok)
        button_sizer.AddButton(self.button_cancel)
        button_sizer.Realize()

        sizer_dirs = wx.BoxSizer(wx.HORIZONTAL)
        sizer_dirs.Add(sizer_dirx, 0, wx.ALL, 5)
        sizer_dirs.Add(sizer_diry, 0, wx.ALL, 5)
        sizer_dirs.Add(sizer_dirz, 0, wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.cb_option, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(sizer_dirs, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.image_panel, 2, wx.EXPAND | wx.ALL,  5)
        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()

    def _bind_events(self):
        self.image_panel.Bind(wx.EVT_PAINT, self.OnPaint)
        #  self.image_panel.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

        self.cb_option.Bind(wx.EVT_COMBOBOX, self.OnSetValues)

        self.spin_from_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_to_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_size_x.Bind(wx.EVT_SPINCTRL, self.OnSetValues)

        self.spin_from_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_to_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_size_y.Bind(wx.EVT_SPINCTRL, self.OnSetValues)

        self.spin_from_z.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_to_z.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnSetValues)
        self.spin_size_z.Bind(wx.EVT_SPINCTRL, self.OnSetValues)

        self.button_ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)

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

        if self.cb_option.GetValue() == 'Blobs':
            self.np_img = np2bitmap(schwarzp.create_blobs(size_x, size_y, 1)[0])
        else:
            self.np_img = np2bitmap(schwarzp.create_schwarzp(
                self.cb_option.GetValue(),
                init_x, end_x,
                init_y, end_y,
                1.0, 1.0,
                size_x,
                size_y,
                1)[0])

    def OnCancel(self, evt):
        self.Destroy()

    def OnOk(self, evt):
        init_x = self.spin_from_x.GetValue()
        end_x = self.spin_to_x.GetValue()
        size_x = self.spin_size_x.GetValue()

        init_y = self.spin_from_y.GetValue()
        end_y = self.spin_to_y.GetValue()
        size_y = self.spin_size_y.GetValue()

        init_z = self.spin_from_z.GetValue()
        end_z = self.spin_to_z.GetValue()
        size_z = self.spin_size_z.GetValue()

        if self.cb_option.GetValue() == 'Blobs':
            schwarp_f = schwarzp.create_blobs(size_x, size_y, size_z)
        else:
            schwarp_f = schwarzp.create_schwarzp(
                self.cb_option.GetValue(),
                init_x, end_x,
                init_y, end_y,
                init_z, end_z,
                size_x,
                size_y,
                size_z)

        schwarp_i16 = imagedata_utils.imgnormalize(schwarp_f, (-1000, 1000))
        Publisher.sendMessage(
            "Create project from matrix", name="SchwarzP", matrix=schwarp_i16
        )

        Publisher.sendMessage('Bright and contrast adjustment image',
                window=255, level=127)
        Publisher.sendMessage('Update window level value',
                              window=255,
                              level=127)
        Publisher.sendMessage('Update slice viewer')

        self.Close()

    def OnSetValues(self, evt):
        self.update_image()
        self.image_panel.Refresh()

    def OnEraseBackground(self, evt):
        pass

    def OnPaint(self, evt):
        dc = wx.PaintDC(self.image_panel)
        dc.SetBackground(wx.Brush('Black'))
        if self.np_img is not None:
            self.render_image(dc)

    def render_image(self, dc):
        psx, psy = self.image_panel.GetSize()
        isx, isy = self.np_img.GetSize()
        cx, cy = psx/2.0 - isx/2.0, psy/2.0 - isy/2.0
        gc = wx.GraphicsContext.Create(dc)
        gc.DrawBitmap(self.np_img, cx, cy, isx, isy)
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
