#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx


# ###########################################################
# Eine MessageBox mit vernünftiger Größe.
class MyMessageBox(wx.Dialog):
  def __init__(self, parent, msg):
    wx.Dialog.__init__(self, parent, wx.ID_ANY, "Message")
    self.msg=msg
    self.InitUI()
    self.Centre()

  # ###########################################################
  # Fenster-Inhalt definieren
  def InitUI(self):
    vsizer=wx.BoxSizer(wx.VERTICAL)

    self.txt=wx.StaticText(self, wx.ID_ANY, self.msg, size=(-1, -1))
    self.but=wx.Button(self, label="ok")

    self.but.Bind(wx.EVT_BUTTON, self.ok)
    self.but.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
    self.but.SetDefault()

    vsizer.Add(self.txt, 0, wx.ALL|wx.EXPAND, 5)
    vsizer.Add(self.but, 0, wx.ALL|wx.ALIGN_CENTER, 5)

    self.SetSizer(vsizer)
    vsizer.Fit(self)
    self.but.SetFocus()

  # ###########################################################
  # Schliesst das Fenster bei Button-Auswahl.
  def ok(self, event):
    self.Close()

  # ###########################################################
  # Schliesst das Fenster bei ESC.
  def OnKeyDown(self, event):
    key=event.GetKeyCode()
    if key==wx.WXK_ESCAPE:
      self.Close()
    else:
      event.Skip()

