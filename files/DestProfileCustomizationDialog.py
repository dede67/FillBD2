#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import os

import Database

import ConfigFile as cfgfile
import Helpers as hlp

# ###########################################################
# Der Dialog zum Festlegen des Zielverzeichnisses, der
# Ziel-Größe und Ziel-Blockgröße.
class DestProfileCustomizationDialog(wx.Dialog):
  def __init__(self, parent, targetFolder, size, blockSize, addblock):
    wx.Dialog.__init__(self, parent, wx.ID_ANY, "Profile Customization")
    self.parent=parent
    self.oldTargetFolder=targetFolder
    self.oldSize=size
    self.oldBlockSize=blockSize
    self.oldAddblock=addblock
    self.db=Database.Database()
    self.InitUI()
    self.Centre()

  # ###########################################################
  # Fenster-Inhalt definieren
  def InitUI(self):
    # alle StaticText-Inhalte in Spalte 0 festlegen
    # ein "" steht für einen vertikalen Platzhalter beim sizer
    label=  [ "Target Profile:",
              "",
              "Profilename:", 
              "Comment:", 
              "Profile Size / Blocksize:", 
              "Folder:", 
              "",
              "",
              "filesystem block size:", 
              "fragment size:", 
              "size of fs in f_frsize units:", 
              "free blocks:", 
              "free blocks for unprivileged users:", 
              "inodes:", "free inodes:", 
              "free inodes for unprivileged users:", 
              "mount flags:", 
              "maximum filename length:",
              "",
              "os.path.ismount:",
              "Media Size:",
              "",
              "Target Size / Blocksize:",
              "Target Filesystems:"
            ]
    # alle StaticText-Inhalte in Spalte 2 festlegen
    # für alle Einträge werden ebenfalls TextCtrl-Objekte in
    # Spalte 1 angelegt, außer bei "-"
    label2= [ "f_bsize", "f_frsize", "f_blocks", "f_bfree", "f_bavail", 
              "f_files", "f_ffree", "f_favail", "f_flag", "f_namemax",
              "-", "", "f_bsize * f_bavail"
            ]
    bgcol="LIGHT BLUE"  # Hintergrundfarbe der doppelklickbaren Felder

    sizer=wx.GridBagSizer(4, 4)

    # erste Spalte mit Feld-Bezeichnungen anlegen
    for y, lab in enumerate(label):
      if lab!="":
        style=wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
        sizer.Add(wx.StaticText(self, label=lab), (y, 0), (1, 1), style, 4)

    # die Spalte für die os.statvfs-Variablennamen anlegen
    for y, lab in enumerate(label2):
      if lab!="-":
        style=wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT
        sizer.Add(wx.StaticText(self, label=lab), (8+y, 2), (1, 1), style, 4)

    # ComboBox "Destination Profile" anlegen
    self.dest_prof=wx.ComboBox(self, size=(150, -1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
    sizer.Add(self.dest_prof,       (0, 1), (1, 2), wx.TOP|wx.RIGHT|wx.EXPAND, 4)
    self.dest_prof.Bind(wx.EVT_COMBOBOX, self.dest_profChanged)

    dpn=self.db.getDestProfileNames()
    self.dest_prof.SetItems(dpn)
    if len(dpn)>0:
      self.dest_prof.SetValue(cfgfile.getLastSelectedDestProfile())

    sizer.Add(wx.StaticLine(self),  (1, 0), (1, 3), wx.ALL|wx.EXPAND, 2)

    # die Felder für die Profil-Daten anlegen
    self.name     =wx.TextCtrl(self, wx.ID_ANY, "", 
                                size=(300, -1), style=wx.TE_READONLY)
    self.comment  =wx.TextCtrl(self, wx.ID_ANY, "",
                                size=(300, -1), style=wx.TE_READONLY)
    self.size     =wx.TextCtrl(self, wx.ID_ANY, "",
                                size=(150, -1), style=wx.TE_READONLY)
    self.blocksize=wx.TextCtrl(self, wx.ID_ANY, "",
                                size=(150, -1), style=wx.TE_READONLY)
    self.folder   =wx.TextCtrl(self, wx.ID_ANY, "", size=(300, -1),
                                style=wx.TE_READONLY)
    sel           =wx.Button(self, wx.ID_ANY, "Select &Target Folder", style=wx.BU_EXACTFIT)
    #Add(item, pos, span=wx.DefaultSpan, flag=0, border=0, userData=None)
    sizer.Add(self.name,            (2, 1), (1, 2), wx.RIGHT|wx.EXPAND, 4)
    sizer.Add(self.comment,         (3, 1), (1, 2), wx.RIGHT|wx.EXPAND, 4)
    sizer.Add(self.size,            (4, 1), (1, 1), wx.RIGHT, 4)
    sizer.Add(self.blocksize,       (4, 2), (1, 1), wx.RIGHT, 4)
    sizer.Add(self.folder,          (5, 1), (1, 2), wx.RIGHT|wx.EXPAND, 4)

    self.size.Bind(wx.EVT_LEFT_DCLICK, self.sizeProfDClick)
    self.blocksize.Bind(wx.EVT_LEFT_DCLICK, self.blocksizeProfDClick)
    self.size.SetBackgroundColour(bgcol)
    self.blocksize.SetBackgroundColour(bgcol)

    sizer.Add(wx.StaticLine(self),  (6, 0), (1, 3), wx.ALL|wx.EXPAND, 2)

    # die Ziel-Verzeichnis-Zeile anlegen
    sizer.Add(sel,                  (7, 0), (1, 1), wx.RIGHT|wx.ALIGN_RIGHT, 4)
    self.targetFolder=wx.TextCtrl(self, wx.ID_ANY, "", size=(300, -1), style=wx.TE_READONLY)
    sizer.Add(self.targetFolder,    (7, 1), (1, 2), wx.RIGHT|wx.EXPAND, 4)
    sel.Bind(wx.EVT_BUTTON, self.selFolderBut)

    # die Felder für die os.statvfs-Infos anlegen
    self.statvfsCtrl=[]
    for y, lab in enumerate(label2):
      if lab=="-":
        self.statvfsCtrl.append(None)
        sizer.Add(wx.StaticLine(self),  (8+y, 1), (1, 1), wx.ALL|wx.EXPAND, 2)
      else:
        self.statvfsCtrl.append(wx.TextCtrl(self, wx.ID_ANY, "", size=(150, -1), style=wx.TE_READONLY))
        sizer.Add(self.statvfsCtrl[y], (8+y, 1))

    self.statvfsCtrl[0].Bind(wx.EVT_LEFT_DCLICK, self.f_bsizeDClick)
    self.statvfsCtrl[12].Bind(wx.EVT_LEFT_DCLICK, self.f_bsize_multipl_f_bavailDClick)
    self.statvfsCtrl[0].SetBackgroundColour(bgcol)
    self.statvfsCtrl[12].SetBackgroundColour(bgcol)

    sizer.Add(wx.StaticLine(self),  (21, 0), (1, 3), wx.ALL|wx.EXPAND, 2)

    # die Zeile mit den relevanten Daten anlegen
    self.fsize     =wx.TextCtrl(self, wx.ID_ANY, "", size=(150, -1))
    self.fblocksize=wx.TextCtrl(self, wx.ID_ANY, "", size=(150, -1))
    self.addBlock1=wx.CheckBox(self, wx.ID_ANY, "Joliet + Rock Ridge (genisoimage)")
    self.addBlock2=wx.CheckBox(self, wx.ID_ANY, "UDF 1.02 (genisoimage)")
    self.addBlock3=wx.CheckBox(self, wx.ID_ANY, "UDF 2.01 (mkudffs)")

    sizer.Add(self.fsize,           (22, 1), (1, 1), wx.RIGHT, 4)
    sizer.Add(self.fblocksize,      (22, 2), (1, 1), wx.RIGHT, 4)
    sizer.Add(self.addBlock1,       (23, 1), (1, 1), wx.RIGHT, 4)
    sizer.Add(self.addBlock2,       (24, 1), (1, 1), wx.RIGHT, 4)
    sizer.Add(self.addBlock3,       (24, 2), (1, 1), wx.RIGHT, 4)

    self.fsize.Bind(wx.EVT_TEXT, self.fsizeChanged)
    self.fblocksize.Bind(wx.EVT_TEXT, self.fblocksizeChanged)
    self.addBlock1.Bind(wx.EVT_CHECKBOX, self.joliet)
    self.addBlock2.Bind(wx.EVT_CHECKBOX, self.udf102)
    self.addBlock3.Bind(wx.EVT_CHECKBOX, self.udf201)

    sizer.Add(wx.StaticLine(self),  (25, 0), (1, 3), wx.ALL|wx.EXPAND, 2)

    # die Zeile mit den Ok/Cancel-Button anlegen
    self.ok=wx.Button(self, wx.ID_OK, "&Ok")
    cancel=wx.Button(self, wx.ID_CANCEL, "&Cancel")
    self.ok.Bind(wx.EVT_BUTTON, self.okBut)
    cancel.Bind(wx.EVT_BUTTON, self.cancelBut)
    h2sizer=wx.BoxSizer(wx.HORIZONTAL)
    h2sizer.Add(self.ok, 0, wx.ALL|wx.ALIGN_RIGHT, 4)
    h2sizer.Add(cancel, 0, wx.ALL|wx.ALIGN_RIGHT, 4)
    sizer.Add(h2sizer, (26, 1), (1, 2))

    # Profil-Felder gemäß ComboBox "Destination Profile" einstellen
    self.setDestProf()
    self.checkForEnableOkButton()
    if self.ok.IsEnabled()==True: # wenn der Ok-Button aktiv ist
      self.ok.SetFocus()          # den per Default auswählen
    else:
      sel.SetFocus()              # sonst den "Select Destination Folder"-Button

    if self.oldTargetFolder!="":
      self.setTargetFolder(self.oldTargetFolder)
    if self.oldSize!=0:
      self.fsize.SetValue(hlp.intToStringWithCommas(self.oldSize))
    if self.oldBlockSize!=0:
      self.fblocksize.SetValue(hlp.intToStringWithCommas(self.oldBlockSize))
    if self.oldAddblock!=None:
      self.setAddBlock(self.oldAddblock)

    self.SetSizer(sizer)
    sizer.Fit(self)

  # ###########################################################
  # ComboBox "Destination Profile" wurde verändert.
  def dest_profChanged(self, event):
    self.setDestProf()

  # ###########################################################
  # Prüft bei Änderung von "self.fsize", ob die drei
  # Rückgabeparameter valide Werte haben und aktiviert oder
  # deaktiviert den Ok-Button entsprechend.
  def fsizeChanged(self, event):
    self.checkForEnableOkButton()
  
  # ###########################################################
  # Prüft bei Änderung von "self.fblocksize", ob die drei
  # Rückgabeparameter valide Werte haben und aktiviert oder
  # deaktiviert den Ok-Button entsprechend.
  def fblocksizeChanged(self, event):
    self.checkForEnableOkButton()

  # ###########################################################
  # Gegenseitiges Abschalten der UDF-Versionen.
  def joliet(self, event):
    if self.addBlock1.GetValue()==True:
      self.addBlock3.SetValue(False)
  def udf102(self, event):
    if self.addBlock2.GetValue()==True:
      self.addBlock3.SetValue(False)
  def udf201(self, event):
    if self.addBlock3.GetValue()==True:
      self.addBlock1.SetValue(False)
      self.addBlock2.SetValue(False)

  # ###########################################################
  # Liefert die drei Checkboxen als einen Interger-Wert.
  def getAddBlock(self):
    rc=0
    rc+=1*int(self.addBlock1.GetValue())
    rc+=2*int(self.addBlock2.GetValue())
    rc+=4*int(self.addBlock3.GetValue())
    return(rc)

  # ###########################################################
  # Setzt die drei Checkboxen gemäß "ab".
  def setAddBlock(self, ab):
    self.addBlock1.SetValue((ab&1)==1)
    self.addBlock2.SetValue((ab&2)==2)
    self.addBlock3.SetValue((ab&4)==4)

  # ###########################################################
  # ComboBox "Destination Profile" wurde verändert.
  def setDestProf(self):
    profData=self.db.getDestProfiles(self.dest_prof.GetValue())
    if len(profData)!=1:
      self.prof_name=self.prof_comment=self.prof_fldrname=""
      self.prof_size=self.prof_blocksize=self.prof_addblock=self.prof_final=0
    else:
      self.prof_name, self.prof_comment, self.prof_size, self.prof_blocksize, \
      self.prof_addblock, self.prof_fldrname, self.prof_final=profData[0]

    self.name.SetValue(self.prof_name)
    self.comment.SetValue(self.prof_comment)
    self.size.SetValue(hlp.intToStringWithCommas(self.prof_size))
    self.blocksize.SetValue(hlp.intToStringWithCommas(self.prof_blocksize))
    self.folder.SetValue(self.prof_fldrname)

    if self.prof_final==1:
      self.setTargetFolder(self.prof_fldrname)
    else:
      # wenn unter "self.prof_fldrname" genau ein Mount gefunden wird, dann
      # diesen Ordner gleich als "self.targetFolder" einstellen
      destPath=self.findSingleMount(self.prof_fldrname)
      if destPath!="":
        self.setTargetFolder(destPath)
      else:
        self.setTargetFolder("")

  # ###########################################################
  # Liefert dem Namen des Mountpoints, der unterhalb von
  # "fldr" existiert, sofern er der einzige Mountpoint
  # unterhalb von "fldr" ist. Ansonsten wird "" geliefert.
  def findSingleMount(self, fldr):
    if fldr=="":
      return("")

    try:
      f=os.listdir(fldr)
    except:
      wx.MessageBox("Unable to access :\n\t"+hlp.forceUTF8(fldr), "Error", wx.OK|wx.ICON_ERROR)
      return("")

    mp_name=""    # Name des Mountpoits (ohne Pfad)
    cnt=0         # Zähler für die Anzahl der Mountpoints
    for i in f:                           # über alle Datei- und Verzeichnis-Namen
      try:
        pthf=os.path.join(fldr, i)        # um Pfad ergänzen
      except:
        wx.MessageBox("Unable to access :\n\t"+fldr+" "+hlp.forceUTF8(i), "Error", wx.OK|wx.ICON_ERROR)
        continue
      if os.path.isdir(pthf)==True:       # wenn es ein Verzeichnis ist...
        if os.path.ismount(pthf)==True:   # und gemountet ist...
          cnt+=1                          # dann zählen
          mp_name=pthf                    # und merken

    if cnt==1:                            # wenn genau ein Mountpoint gefunden wurde
      return(mp_name)
    return("")

  # ###########################################################
  # Doppelklicks für vier Felder verarbeiten.
  def sizeProfDClick(self, event):
    self.fsize.SetValue(self.size.GetValue())
    self.checkForEnableOkButton()
  def blocksizeProfDClick(self, event):
    self.fblocksize.SetValue(self.blocksize.GetValue())
    self.checkForEnableOkButton()
  def f_bsizeDClick(self, event):
    self.fblocksize.SetValue(self.statvfsCtrl[0].GetValue())
    self.checkForEnableOkButton()
  def f_bsize_multipl_f_bavailDClick(self, event):
    self.fsize.SetValue(self.statvfsCtrl[12].GetValue())
    self.checkForEnableOkButton()

  # ###########################################################
  # "Select Destination Folder"-Button wurde gewählt.
  def selFolderBut(self, event):
    dlg=wx.DirDialog(self, message="Destination Folder", defaultPath=self.prof_fldrname)
    if dlg.ShowModal()!=wx.ID_OK:
      dlg.Destroy()
      return
    
    destPath=dlg.GetPath()#.encode("utf8")
    dlg.Destroy()
    if os.access(destPath, os.F_OK|os.W_OK)==True:
      self.setTargetFolder(destPath)
    else:
      if destPath=="":
        wx.MessageBox("Unable to access the selected folder!", "Error", wx.OK|wx.ICON_ERROR)
      else:
        wx.MessageBox("Unable to access :\n\t"+destPath, "Error", wx.OK|wx.ICON_ERROR)

  # ###########################################################
  # Setzt den Inhalt von "self.targetFolder" auf "destPath" und
  # setzt ebenfalls alle abhängigen Felder.
  def setTargetFolder(self, destPath):
    self.targetFolder.SetValue(destPath)

    # die Felder für die os.statvfs-Infos mit Inhalten füttern
    try:  # Bug in os.statvfs() umschiffen....
      sz=os.statvfs(destPath)
      f_bsize=sz.f_bsize
      f_bavail=sz.f_bavail
    except Exception, e:    # ggf. UnicodeEncodeError
      sz=""
      f_bsize=0
      f_bavail=0
      if destPath!="":
        wx.MessageBox(str(e)+"\n\t"+destPath, "Error", wx.OK|wx.ICON_ERROR)

    if len(sz)==0:
      for i in range(10):
        self.statvfsCtrl[i].SetValue("0")
    else:
      for i in range(len(sz)):
        self.statvfsCtrl[i].SetValue(hlp.intToStringWithCommas(sz[i]))

    isMount=os.path.ismount(destPath)
    self.statvfsCtrl[11].SetValue(str(isMount))
    self.statvfsCtrl[12].SetValue(hlp.intToStringWithCommas(f_bsize*f_bavail))

    if isMount==True:
      # wenn das gewählte Zielverzeichnis direkt ein Mount ist, dessen Daten nehmen
      self.fsize.SetValue(hlp.intToStringWithCommas(f_bsize*f_bavail))
      self.fblocksize.SetValue(hlp.intToStringWithCommas(f_bsize))
    else:
      # wenn das gewählte Zielverzeichnis kein direkter Mount ist, die Daten aus dem Profil nehmen
      self.fsize.SetValue(hlp.intToStringWithCommas(self.prof_size))
      self.fblocksize.SetValue(hlp.intToStringWithCommas(self.prof_blocksize))
    self.setAddBlock(self.prof_addblock)
    self.checkForEnableOkButton()

  # ###########################################################
  # Stellt den Ok-Button auf Enabled, sofern:
  #  - der Ziel-Ordner eingestellt wurde und zugreifbar ist
  #  - die Zieldatenträger-Größe >0 ist
  #  - die Zieldatenträger-Blockgröße >0 ist
  def checkForEnableOkButton(self):
    destPathIsAccessable=os.access(self.targetFolder.GetValue(), os.F_OK|os.W_OK)
    size=hlp.stringWithCommasToInt(self.fsize.GetValue())
    blocksize=hlp.stringWithCommasToInt(self.fblocksize.GetValue())

    self.targetFolder.SetBackgroundColour(wx.NullColor)
    self.fsize.SetBackgroundColour(       wx.NullColor)
    self.fblocksize.SetBackgroundColour(  wx.NullColor)
    self.targetFolder.SetToolTip( wx.ToolTip.Enable(False))
    self.fsize.SetToolTip(        wx.ToolTip.Enable(False))
    self.fblocksize.SetToolTip(   wx.ToolTip.Enable(False))

    if size>0 and blocksize>0 and size%blocksize!=0:
        self.fsize.SetBackgroundColour("MAGENTA")
        self.fsize.SetToolTip(wx.ToolTip("<size> can only be a multiple of <blocksize>"))
    fldrSize=hlp.stringWithCommasToInt(self.statvfsCtrl[12].GetValue())

    if destPathIsAccessable==True and size>0 and blocksize>0 and size<=fldrSize:
      self.ok.Enable()
      return
    self.ok.Disable()

    if destPathIsAccessable!=True:
      self.targetFolder.SetBackgroundColour("MAGENTA")
      self.targetFolder.SetToolTip(wx.ToolTip("<Target Folder> must be accessible"))

    if size<=0:
      self.fsize.SetBackgroundColour("MAGENTA")
      self.fsize.SetToolTip(wx.ToolTip("<Target Size> must be greater than zero"))

    if blocksize<=0:
      self.fblocksize.SetBackgroundColour("MAGENTA")
      self.fblocksize.SetToolTip(wx.ToolTip("<Target Blocksize> must be greater than zero"))

    if size>fldrSize:
      self.fsize.SetBackgroundColour("MAGENTA")
      self.fsize.SetToolTip(wx.ToolTip("<Target Size> must be less than or equal <Media Size>"))

  # ###########################################################
  # Cancel-Button wurde gewählt.
  def cancelBut(self, event):
    self.EndModal(wx.ID_CANCEL)

  # ###########################################################
  # Ok-Button wurde gewählt.
  def okBut(self, event):
    cfgfile.setLastSelectedDestProfile(self.dest_prof.GetValue())
    self.EndModal(wx.ID_OK)

  # ###########################################################
  # Liefert die Daten aus "self.targetFolder", "self.fsize",
  # "self.fblocksize" und self.addBlock(1-3) als
  # Tupel (str, int, int, int).
  def getData(self):
    return( ( self.targetFolder.GetValue(),
              hlp.stringWithCommasToInt(self.fsize.GetValue()),
              hlp.stringWithCommasToInt(self.fblocksize.GetValue()),
              self.getAddBlock()
            )
          )

