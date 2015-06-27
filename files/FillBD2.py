#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import wx.lib.mixins.listctrl as listmix
import os
import time
import sqlite3


import Database
import FileOrFolderDict
import MyMessageBox
import SelectFiles
import SetupDialog
import DestProfileCustomizationDialog
import ExportDialog
import ConnectedFiles

import ConfigFile as cfgfile
import Helpers as hlp

ignore_symlinks_g=True  # False kann es [noch] nicht

VERSION="2.2"
#
# 2.0   04.10.2014  initiale Version mit GUI
# 2.1   11.10.2014  Aufteilung der Größenberechnung bei Kombi-Dateisystemen
# 2.1a  23.10.2014  automatisches Öffnen von "DestProfileCustomizationDialog" nach Programmstart
# 2.1b  14.04.2015  Erkennung von Datei-Zusammengehörigkeit via ConnectedFiles zugefügt
# 2.1c  09.05.2015  ErrorIcon bei Dateien > 4294967295 Byte auf FAT32
# 2.2   20.05.2015  verschobene Dateien werden nach ExportDialog aus dem ListCtrl2 entfernt

# class FillBD2Frame(wx.Frame)
# class FileDrop(wx.FileDropTarget)
# class insertErrorCollector()
# class MyListCtrl(wx.ListCtrl)
# class FillDB2ListCtrl(wx.Panel, listmix.ColumnSorterMixin)
# class FillBD2(wx.Panel)

# ###########################################################
# Der Fenster-Rahmen für fillBD2.
class FillBD2Frame(wx.Frame):
  def __init__(self, pos, size):
    wx.Frame.__init__(self, None, wx.ID_ANY, "FillBD2", pos=pos, size=size)
    if pos==wx.DefaultPosition:
      self.Centre()
    self.Bind(wx.EVT_CLOSE, self.onClose)
    FillBD2(self)

  # ###########################################################
  # speichert die aktuelle Windows-Position und -Größe.
  def onClose(self, event):
    pos=self.GetScreenPosition()
    size=self.GetSizeTuple()
    cfgfile.setWindowSize(pos, size)
    event.Skip()





# ###########################################################
# Eine kleine Klasse, um neue Dateien via Drag&Drop ins
# ListCtrl1 laden zu können.
class FileDrop(wx.FileDropTarget):
  def __init__(self, parent, ctrl):
    wx.FileDropTarget.__init__(self)
    self.parent=parent
    self.ctrl=ctrl

  # ###########################################################
  # Dateien oder Ordner wurden ins Fenster gedropped.
  def OnDropFiles(self, x, y, filenames):
    if len(filenames)>900:
      wx.MessageBox("Too many files for the root directory!", "Error", wx.OK|wx.ICON_ERROR)
      return

    unable2access=""
    notLoaded=""
    deleted=""
    nameDupe=""
    files=self.ctrl.data

    wx.BeginBusyCursor()
    wx.Yield()
    ec=insertErrorCollector(self.parent)
    for fn in filenames:
      if files.isValid(fn)==False:
        ec.add(2, fn)
        continue

      size, sizeAdj, errors=self.parent._getFileSize(fn)
      if errors!="":
        ec.add(2, errors)
        errFlag=True
      else:
        errFlag=False

      sizeAdj+=self.parent.getDirectorySize(os.path.basename(fn))

      rc=files.insertFileOrFolder(fn, size, sizeAdj, errFlag)
      if rc>0:
        ec.add(rc, fn)

    self.parent.fillListCtrl(self.ctrl)
    ec.show()

    self.parent.restoreSort(self.parent.list_panel1)

    wx.EndBusyCursor()
    wx.Yield()
    return




# ###########################################################
# Ein Sammler für die gemeinsame Ausgabe von Fehlermeldungen
# von FileOrFolderDict.insertFileOrFolder().
class insertErrorCollector():
  def __init__(self, parent):
    self.parent=parent
    self.deleted=""         # sammelt errorcode(1)
    self.unable2access=""   # sammelt errorcode(2)
    self.notLoaded=""       # sammelt errorcode(3 & 4)
    self.nameDupe=""        # sammelt errorcode(5)

  # ###########################################################
  # Fügt einen Fehlercode samt zugehörigem Dateinamen zu.
  def add(self, errorcode, filename):
    if len(filename)>2:
      if filename[:2]=="\n\t":  # wenn String schon mit \n\t beginnt
        filename=filename[2:]   # dann die zwei Byte abschneiden
    if errorcode==1:
      self.deleted+=      "\n\t"+filename
    elif errorcode==2:
      self.unable2access+="\n\t"+filename
    elif errorcode in (3, 4):
      self.notLoaded+=    "\n\t"+filename
    elif errorcode==5:
      self.nameDupe+=     "\n\t"+filename

  # ###########################################################
  # Zeigt die gesammelten Fehlermeldungen mit ihren jeweiligen
  # Dateinamen an.
  def show(self):
    maxlines=10
    bigmsg=""
    ul="\n"+"-"*100
    self.unable2access= self.cutOffLines(self.unable2access,  maxlines)
    self.notLoaded=     self.cutOffLines(self.notLoaded,      maxlines)
    self.deleted=       self.cutOffLines(self.deleted,        maxlines)
    self.nameDupe=      self.cutOffLines(self.nameDupe,       maxlines)
    if self.unable2access!="": bigmsg+="\nUnable to access:"       +ul+self.unable2access +"\n"
    if self.notLoaded    !="": bigmsg+="\nAlready in list:"        +ul+self.notLoaded     +"\n"
    if self.deleted      !="": bigmsg+="\nSubfolders removed for:" +ul+self.deleted       +"\n"
    if self.nameDupe     !="": bigmsg+="\nDupe for target folder:" +ul+self.nameDupe      +"\n"
    if bigmsg!="":
      dlg=MyMessageBox.MyMessageBox(self.parent, bigmsg)
      dlg.ShowModal()
      dlg.Destroy()

  # ###########################################################
  # Liefert einen String, der maximal die ersten "lines"+1
  # Zeilen von "strg" enthält.
  def cutOffLines(self, strg, lines):
    lns=strg.count("\n")
    if lns>lines:
      endpos=self.findnth(strg, "\n", lines)
      strg=strg[:endpos]+"\nand %i more files"%(lns-lines)
    return(strg)

  # ###########################################################
  # Find the nth occurrence of substring in a string
  # http://stackoverflow.com/a/1884151/3588613
  def findnth(self, haystack, needle, n):
    parts= haystack.split(needle, n+1)
    if len(parts)<=n+1:
        return -1
    return len(haystack)-len(parts[-1])-len(needle)





# ###########################################################
# listmix.ColumnSorterMixin will das so....
class MyListCtrl(wx.ListCtrl):
  def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
    wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
    self.parent=parent
    self.data=FileOrFolderDict.FileOrFolderDict()





# ###########################################################
# Ein Panel für das ListCtrl mit ColumnSorterMixin.
# Dank an Mike Driscoll (http://stackoverflow.com/a/25393430/3588613)
class FillDB2ListCtrl(wx.Panel, listmix.ColumnSorterMixin):
  def __init__(self, parent, ctrl_nr=1):
    wx.Panel.__init__(self, parent, wx.ID_ANY, style=wx.WANTS_CHARS)
    self.parent=parent
    self.ctrl_nr=ctrl_nr

    self.lastSortOrder=cfgfile.getColSort(ctrl_nr)
    self.list_ctrl=MyListCtrl(self, style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)

    self.il=wx.ImageList(16, 16)
    self.c1iinfo= self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_REPORT_VIEW,  wx.ART_OTHER, (16, 16)))
    self.empty=   self.il.Add(wx.EmptyBitmap(0, 0))
    self.c1ifile= self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE,  wx.ART_OTHER, (16, 16)))
    self.c1ifldr= self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER,       wx.ART_OTHER, (16, 16)))
    self.sm_up=   self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP,        wx.ART_OTHER, (16, 16)))
    self.sm_dn=   self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN,      wx.ART_OTHER, (16, 16)))
    self.errico=  self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_ERROR,        wx.ART_OTHER, (16, 16)))

    colWidthList=cfgfile.getColWidth(self.ctrl_nr)
    # leere/unsichtbare Spalte anlegen, weil die Spalte0 Probleme mit der BMP-Darstellung hat
    self.list_ctrl.InsertColumn(0, '',                                    width=0)
    if self.ctrl_nr==1:
      self.list_ctrl.InsertColumn(1, 'path',                              width=colWidthList[0])
      self.list_ctrl.InsertColumn(2, 'name',                              width=colWidthList[1])
    elif self.ctrl_nr==2:
      self.list_ctrl.InsertColumn(1, '',                                  width=0)
      self.list_ctrl.InsertColumn(2, 'name',                              width=colWidthList[0])

    if self.ctrl_nr==1:
      self.list_ctrl.InsertColumn(3, 'size(real)',  wx.LIST_FORMAT_RIGHT, width=colWidthList[2])
      self.list_ctrl.InsertColumn(4, 'size(dest)',  wx.LIST_FORMAT_RIGHT, width=colWidthList[3])
      listmix.ColumnSorterMixin.__init__(self, 5)
    elif self.ctrl_nr==2:
      self.list_ctrl.InsertColumn(3, 'size(dest)',  wx.LIST_FORMAT_RIGHT, width=colWidthList[1])
      listmix.ColumnSorterMixin.__init__(self, 4)

    self.list_ctrl.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
    self.list_ctrl.Bind(wx.EVT_LIST_COL_END_DRAG, self.onColResize)

    self.list_ctrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

    sizer=wx.BoxSizer(wx.VERTICAL)
    sizer.Add(self.list_ctrl, 1, wx.EXPAND)
    self.SetSizer(sizer)
    self.SortListItems(self.lastSortOrder[0], self.lastSortOrder[1])

  # ###########################################################
  # Nach Änderung der Breite einer Spalte die neue Breite im
  # ConfigFile speichern.
  def onColResize(self, event):
    if self.ctrl_nr==1:
      visibleCols=(1, 2, 3, 4)
    elif self.ctrl_nr==2:
      visibleCols=(2, 3)
    else:
      return
    lst=[]
    for c in visibleCols:
      lst.append(self.list_ctrl.GetColumnWidth(c))
    cfgfile.setColWidth(self.ctrl_nr, lst)

  # ###########################################################
  # Liefert die Bitmap-Indices für die Spalten-Überschriften.
  def GetSortImages(self):
    return(self.sm_dn, self.sm_up)

  # ###########################################################
  # Speichert die jew. zuletzt eingestellte Sortierreihenfolge.
  def OnSortOrderChanged(self):
    self.lastSortOrder=self.GetSortState()
    cfgfile.setColSort(self.ctrl_nr, self.lastSortOrder)

  # ###########################################################
  # Will listmix.ColumnSorterMixin haben.
  def GetListCtrl(self):
   return(self.list_ctrl)
  def OnColClick(self, event):
    self.addColToDict()
    event.Skip()

  # ###########################################################
  # Kopiert "self.list_ctrl.data.obj" nach "self.itemDataMap"
  # und erweitert es dabei um eine Spalte(0).
  def addColToDict(self):
    self.itemDataMap={}
    # hier wird die erste (unsichtbare) Spalte zugefügt
    for key, data in self.list_ctrl.data.obj.items():
      self.itemDataMap.update({data.index : ( data.index,       \
                                              data.foldername,  \
                                              data.filename,    \
                                              data.size,        \
                                              data.sizeAdj)})




# ###########################################################
# Das eigentliche Fenster von FillBD2.
class FillBD2(wx.Panel):
  def __init__(self, parent):
    wx.Panel.__init__(self, parent, wx.ID_ANY, style=wx.WANTS_CHARS)

    self.db=Database.Database()

    self.targetFolder=""                # Zielverzeichnis
    self.size=0                         # Größe des Zieldatenträgers
    self.blockSize=0                    # Blockgröße auf dem Zieldatenträger
    self.addblock=None
    self.calcTime=cfgfile.getCalcTime() # maximale Rechendauer für SelectFiles() [Sekunden]

    self.parent=parent

    # Quasi-Toolbar anlegen
    self.setup=wx.Button(self, wx.ID_ANY, "&Setup Profiles")
    self.setup.Bind(wx.EVT_BUTTON, self.setupBut)

    self.choose_dest=wx.Button(self, wx.ID_ANY, "Choose &Target")
    self.choose_dest.Bind(wx.EVT_BUTTON, self.choose_destBut)

    base_profile_txt=wx.StaticText(self, label="Source &Profile:")
    self.base_profile=wx.ComboBox(self, size=(150, -1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
    self.base_profile.Disable()
    self.base_profile.Bind(wx.EVT_COMBOBOX, self.base_profileChanged)
    self.fillComboBoxes()

    self.fillTarget=wx.Button(self, wx.ID_ANY, "&Fill Target",  (-1, -1), wx.DefaultSize)
    self.fillTarget.Bind(wx.EVT_BUTTON, self.fillTargetBut)

    self.export=wx.Button(self, wx.ID_ANY, "&Export",  (-1, -1), wx.DefaultSize)
    self.export.Bind(wx.EVT_BUTTON, self.exportBut)

    bmp=wx.ArtProvider.GetBitmap(wx.ART_HELP_PAGE, wx.ART_OTHER, (16,16))
    self.info=wx.BitmapButton(self, wx.ID_ANY, bmp)
    self.info.Bind(wx.EVT_BUTTON, self.aboutDialog)

    blksize_txt=wx.StaticText(self, label="Blocksize:")
    self.blksize=wx.TextCtrl(self, wx.ID_ANY, "", size=(70, -1), style=wx.TE_READONLY|wx.TE_RIGHT)
    targtFldr_txt=wx.StaticText(self, label="Target Folder:")
    self.targtFldr=wx.TextCtrl(self, wx.ID_ANY, "", size=(250, -1), style=wx.TE_READONLY)

    # die beiden Haupt-ListCtrls anlegen
    self.list_panel1=FillDB2ListCtrl(self, 1)
    self.list_panel2=FillDB2ListCtrl(self, 2)
    self.list_panel1.list_ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick1)
    self.list_panel2.list_ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick2)

    # die Summen-Zeile anlegen
    s=wx.TE_READONLY|wx.TE_RIGHT
    self.lp1_size   =wx.TextCtrl(self, wx.ID_ANY, "", size=(120, -1), style=s)
    self.lp1_sizeAdj=wx.TextCtrl(self, wx.ID_ANY, "", size=(120, -1), style=s)
    self.lp2_sizeAdj=wx.TextCtrl(self, wx.ID_ANY, "", size=(120, -1), style=s)
    self.lp2_sizeRem=wx.TextCtrl(self, wx.ID_ANY, "", size=(120, -1), style=s)
    txt_lp1_size    =wx.StaticText(self, label="sum(size(real)):")
    txt_lp1_sizeAdj =wx.StaticText(self, label="sum(size(dest)):")
    txt_lp2_sizeAdj =wx.StaticText(self, label="sum(size(dest)):")
    txt_lp2_sizeRem =wx.StaticText(self, label="size(remain):")

    vsizer=wx.BoxSizer(wx.VERTICAL)     # der oberste Sizer
    bsizer=wx.BoxSizer(wx.HORIZONTAL)   # der Sizer für die Quasi-Toolbar
    hsizer=wx.BoxSizer(wx.HORIZONTAL)   # der Sizer für die beiden ListCtrls

    h1sizer=wx.BoxSizer(wx.HORIZONTAL)  # der Sizer für die Summen unter ListCtrl1
    h2sizer=wx.BoxSizer(wx.HORIZONTAL)  # der Sizer für die Summen unter ListCtrl2
    h3sizer=wx.BoxSizer(wx.HORIZONTAL)  # der Sizer für h1sizer und h2sizer

    bsizer.Add(self.setup,        0, wx.ALL, 2)
    bsizer.Add(self.choose_dest,  0, wx.ALL, 2)
    bsizer.Add(base_profile_txt,  0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 2)
    bsizer.Add(self.base_profile, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 2)
    bsizer.Add(self.fillTarget,   0, wx.ALL, 2)
    bsizer.Add(self.export,       0, wx.ALL, 2)
    bsizer.AddStretchSpacer()
    bsizer.Add(self.info,         0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 2)
    bsizer.Add(blksize_txt,       0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 10)
    bsizer.Add(self.blksize,      0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 2)
    bsizer.Add(targtFldr_txt,     0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 10)
    bsizer.Add(self.targtFldr,    0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 2)

    hsizer.Add(self.list_panel1, 20, wx.ALL|wx.EXPAND, 1)
    hsizer.Add(self.list_panel2, 11, wx.ALL|wx.EXPAND, 1)

    h1sizer.AddStretchSpacer()
    h1sizer.Add(txt_lp1_size,     0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 1)
    h1sizer.Add(self.lp1_size,    0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 1)
    h1sizer.Add(txt_lp1_sizeAdj,  0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 30)
    h1sizer.Add(self.lp1_sizeAdj, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 1)

    h2sizer.AddStretchSpacer()
    h2sizer.Add(txt_lp2_sizeAdj,  0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 1)
    h2sizer.Add(self.lp2_sizeAdj, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 1)
    h2sizer.Add(txt_lp2_sizeRem,  0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 30)
    h2sizer.Add(self.lp2_sizeRem, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 1)

    h3sizer.Add(h1sizer, 10, wx.ALL|wx.EXPAND|wx.ALIGN_RIGHT, 1)
    h3sizer.Add(h2sizer,  8, wx.ALL|wx.EXPAND|wx.ALIGN_RIGHT, 1)

    vsizer.Add(bsizer,  0, wx.ALL|wx.EXPAND, 1)
    vsizer.Add(hsizer,  1, wx.ALL|wx.EXPAND, 1)
    vsizer.Add(h3sizer, 0, wx.ALL|wx.EXPAND, 1)

    self.SetSizer(vsizer)
    vsizer.Fit(self)
    self.choose_dest.SetFocus()
    wx.CallLater(100, self.choose_destBut)

  # ###########################################################
  # Stellt die zuletzt eingestellte Sortierreihenfolge wieder
  # her.
  def restoreSort(self, ctrl, topItem=0):
    if ctrl.lastSortOrder[0]>=0:
      ctrl.addColToDict()
      ctrl.SortListItems(ctrl.lastSortOrder[0], ctrl.lastSortOrder[1])
      ctrl.list_ctrl.EnsureVisible(ctrl.list_ctrl.GetItemCount()-1)
      ctrl.list_ctrl.EnsureVisible(topItem)

  # ###########################################################
  # Verarbeitet Änderungen an der Auswahl in "Source Profile"
  def base_profileChanged(self, event):
    basePathList=[]
    if self.base_profile.GetValue()!="":
      sp=self.db.getBaseProfiles(self.base_profile.GetValue())
      # sp: name, comment, hiddenfiles, folderList
      if len(sp)>0:
        basePathList=sp[0][3]  # FolderList
    self.getFilesFromBasePath(basePathList, sp[0][2])
    self.restoreSort(self.list_panel1)

  # ###########################################################
  # Füttert die ComboBox "base_profile" mit Inhalt.
  def fillComboBoxes(self):
    bpn=self.db.getBaseProfileNames()
    self.base_profile.SetItems(bpn)

  # ###########################################################
  # Schaltet Drag&Drop für "self.list_panel1.list_ctrl" frei
  # und aktiviert die ComboBox "self.base_profile".
  def enableListCtrl1(self):
    self.list_panel1.list_ctrl_dt=FileDrop(self, self.list_panel1.list_ctrl)
    self.list_panel1.list_ctrl.SetDropTarget(self.list_panel1.list_ctrl_dt)
    self.base_profile.Enable()

  # ###########################################################
  # Button "Setup Profiles" wurde gewählt.
  def setupBut(self, event):
    dlg=SetupDialog.SetupDialog(self, self.calcTime)
    dlg.ShowModal()
    self.calcTime=dlg.getData()
    cfgfile.setCalcTime(self.calcTime)
    dlg.Destroy()
    self.fillComboBoxes()

  # ###########################################################
  # Button "Choose Destination" wurde gewählt.
  def choose_destBut(self, event=0):
    lastProfile=cfgfile.getLastSelectedDestProfile()  # merken, um es bei NO im Folgedialog ggf. zurücksetzen zu können
    dlg=DestProfileCustomizationDialog.DestProfileCustomizationDialog(self, 
                                        self.targetFolder, self.size, self.blockSize, self.addblock)
    if dlg.ShowModal()!=wx.ID_OK:
      dlg.Destroy()
      return

    targetFolder, size, blockSize, addblock=dlg.getData()
    dlg.Destroy()
    if (self.blockSize>0 and self.blockSize!=blockSize) or (self.addblock!=None and self.addblock!=addblock):
      # Blocksize wurde verändert!!!
      if len(self.list_panel1.list_ctrl.data.obj)>0 or len(self.list_panel2.list_ctrl.data.obj)>0:
        # es befinden sich schon Objekte in mind. einem der ListCtrls
        rc=wx.MessageBox("Blocksize or filesystems changed!\nRemove all files from both lists?",
                          "Confirm", wx.YES_NO, self)
        if rc!=wx.YES:
          cfgfile.setLastSelectedDestProfile(lastProfile)
          return
        self.deleteAllFromListCtrl1(0)
        self.deleteAllFromListCtrl2(0)
        self.base_profile.SetValue("")

    self.targetFolder=targetFolder
    self.size=size
    self.blockSize=blockSize
    self.addblock=addblock
    self.__updateSum(self.list_panel1.list_ctrl, 1)
    self.__updateSum(self.list_panel2.list_ctrl, 2)

    self.blksize.SetValue(hlp.intToStringWithCommas(self.blockSize))
    self.targtFldr.SetValue(targetFolder)
    if self.isEmptyFolder(targetFolder)!=True:
      self.targtFldr.SetBackgroundColour("YELLOW")
      self.targtFldr.SetToolTip(wx.ToolTip("Folder not empty!"))
    else:
      self.targtFldr.SetBackgroundColour(wx.NullColor)
      self.targtFldr.SetToolTip(wx.ToolTip.Enable(False))

    self.enableListCtrl1()

  # ###########################################################
  # Liefert True, wenn der Ordner "folder" leer ist, sonst False.
  def isEmptyFolder(self, folder):
    return(len(os.listdir(folder))==0)

  # ###########################################################
  # Button "Fill Target" wurde gewählt.
  def fillTargetBut(self, event):
    fileList1=[]
    fileList2=[]
    topItem1=self.list_panel1.list_ctrl.GetTopItem()
    topItem2=self.list_panel2.list_ctrl.GetTopItem()
    for key, data in self.list_panel1.list_ctrl.data.obj.items():    
      fileList1.append((data.fullname, data.sizeAdj, data.size))
    if len(fileList1)==0:
      return

    for key, data in self.list_panel2.list_ctrl.data.obj.items():
      fileList2.append((data.fullname, data.sizeAdj, data.size))

    # sortieren nach sizeAdj
    fileList1=sorted(fileList1, key=lambda x: x[1], reverse=True)

    destSize=self.size
    blockSize=self.blockSize

    # Restkapazität auf Dest bestimmen
    sd=0
    for i in fileList2:
      sd+=i[1]
    destSize-=sd

    sf=SelectFiles.SelectFiles(self, fileList1, destSize, blockSize, self.calcTime)
    flst, fsum=sf.getFiles()
    for fullname, sizeAdj, size in flst:
      d=self.list_panel1.list_ctrl.data.getByFullname(fullname)
      self.list_panel2.list_ctrl.data.insertFileOrFolder(fullname, size, sizeAdj, d.hasErrors)
      self.list_panel1.list_ctrl.data.remove(fullname)

    self.fillListCtrl(self.list_panel1.list_ctrl, 1)    
    self.fillListCtrl(self.list_panel2.list_ctrl, 2)
    self.restoreSort(self.list_panel1, topItem1)
    self.restoreSort(self.list_panel2, topItem2)

  # ###########################################################
  # Button "Export" wurde gewählt.
  def exportBut(self, event):
    lst=[]
    for key in self.list_panel2.list_ctrl.data.obj.keys():
      lst.append(key) # umkopieren, um in der nächsten for-loop ggf. zu löschen 

    dlg=ExportDialog.ExportDialog(self, self.targtFldr.GetValue(), \
                                        self.list_panel2.list_ctrl.data.obj, \
                                        self.addblock)

    if dlg.ShowModal()!=wx.ID_OK:
      dlg.Destroy()
      return

    for fn in lst:  # ggf. verschobene Dateien aus dem ListCtrl2 entfernen
      if os.path.exists(fn)==False:
        self.list_panel2.list_ctrl.data.remove(fn)
    self.fillListCtrl(self.list_panel2.list_ctrl, 2)
    topItem2=self.list_panel2.list_ctrl.GetTopItem()
    self.restoreSort(self.list_panel2, topItem2)

    dlg.Destroy()

  # ###########################################################
  # About-Box ausgeben
  def aboutDialog(self, event):
    info=wx.AboutDialogInfo()
    info.SetName("FillBD2")
    info.SetVersion(VERSION)
    info.SetCopyright("D.A.  (09.2014)")
    info.SetDescription("A tool to find a set of files whose total size is as close as possible below a defined size.")
    info.SetLicence("""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.""")
    info.AddDeveloper("Detlev Ahlgrimm")
    wx.AboutBox(info)


  # ###########################################################
  # Liefert den Key aus dem Dictionary "dic" von dem Satz, bei
  # dem die ersten drei Werte aus "data" mit den entspr. Werten
  # aus dem dic-Value übereinstimmen.
  def findInDict(self, dic, data):
    for k, d in dic.items():
      if d[0]==data[0] and d[1]==data[1] and d[2]==data[2]:
        return(k)
    return(None)

  # ###########################################################
  # Setzt die Summen-Felder gemäß der Summen in den entspr.
  # Spalten in "ctrl.data".
  def __updateSum(self, ctrl, ctrl_nr):
    size=sizeAdj=0
    for key, data in ctrl.data.obj.items():
      size+=data.size
      sizeAdj+=data.sizeAdj

    if ctrl_nr==1:
      self.lp1_size.SetValue(hlp.intToStringWithCommas(size))
      self.lp1_sizeAdj.SetValue(hlp.intToStringWithCommas(sizeAdj))
      if sizeAdj<self.size:
        self.lp1_sizeAdj.SetBackgroundColour("YELLOW")
        self.lp1_sizeAdj.SetToolTip(wx.ToolTip("Not enough files to fill target"))
      else:
        self.lp1_sizeAdj.SetBackgroundColour(wx.NullColor)
        self.lp1_sizeAdj.SetToolTip(wx.ToolTip.Enable(False))
    else:
      self.lp2_sizeAdj.SetValue(hlp.intToStringWithCommas(sizeAdj))
      remSize=self.size-sizeAdj
      self.lp2_sizeRem.SetValue(hlp.intToStringWithCommas(remSize))
      if remSize<0:
        self.lp2_sizeRem.SetBackgroundColour("YELLOW")
        self.lp2_sizeRem.SetToolTip(wx.ToolTip("Files do not fit on target"))
      else:
        self.lp2_sizeRem.SetBackgroundColour(wx.NullColor)
        self.lp2_sizeRem.SetToolTip(wx.ToolTip.Enable(False))

  # ###########################################################
  # Füllt das ListCtrl "ctrl" mit dem Inhalt aus "ctrl.data".
  def fillListCtrl(self, ctrl, ctrl_nr=1):
    ctrl.DeleteAllItems()
    ctrl.Refresh()
    self.__updateSum(ctrl, ctrl_nr)

    index=0
    for key, data in ctrl.data.obj.items():
      ctrl.InsertStringItem(index, str(data.index))  # dummy

      if ctrl_nr==1:
        if data.isFolder==True:
          # Ordner mit Folder-Icon einfügen
          if data.hasErrors==True:
            ctrl.SetStringItem(index, 1, data.foldername, self.list_panel1.errico)
          else:
            ctrl.SetStringItem(index, 1, data.foldername, self.list_panel1.c1ifldr)
        elif data.isFile==True:
          if self.addblock==0 and data.size>4294967295:
            ctrl.SetStringItem(index, 1, data.foldername, self.list_panel1.errico)
          else:
            # Datei mit File-Icon einfügen
            ctrl.SetStringItem(index, 1, data.foldername, self.list_panel1.c1ifile)

      if ctrl_nr==1:
        # Datei einfügen
        ctrl.SetStringItem(index, 2, data.filename)
      else:
        if data.isFolder==True:
          if data.hasErrors==True:
            ctrl.SetStringItem(index, 2, data.filename, self.list_panel1.errico)
          else:
            ctrl.SetStringItem(index, 2, data.filename, self.list_panel1.c1ifldr)
        elif data.isFile==True:
          ctrl.SetStringItem(index, 2, data.filename, self.list_panel1.c1ifile)

      if ctrl_nr==1:
        ctrl.SetStringItem(index, 3, hlp.intToStringWithCommas(data.size))
        ctrl.SetStringItem(index, 4, hlp.intToStringWithCommas(data.sizeAdj))
      else:
        ctrl.SetStringItem(index, 3, hlp.intToStringWithCommas(data.sizeAdj))

      ctrl.SetItemImage(index, 1)
      ctrl.SetItemData(index, data.index)
      index+=1
    ctrl.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

  # ###########################################################
  # Lädt die Dateien in den Basisordnern ins self.list_panel1.
  def getFilesFromBasePath(self, folderList, hiddenFiles):
    self.list_panel1.list_ctrl.DeleteAllItems()
    files=self.list_panel1.list_ctrl.data
    files.clear()
    ec=insertErrorCollector(self)

    wx.BeginBusyCursor()
    wx.Yield()

    for i in folderList:
      try:
        f=os.listdir(i)
      except:
        ec.add(2, i)
        continue
      for j in f:
        if j[0]=="." and hiddenFiles==0:  # wenn hiddenFile und unerwünscht
          continue                        # dann überspringen
        try:
          fn=os.path.join(i, j)
        except:
          ec.add(2, hlp.forceUTF8(i)+"/"+hlp.forceUTF8(j))
          continue

        if files.isValid(fn)==False:
          ec.add(2, fn)
          continue

        size, sizeAdj, errors=self._getFileSize(fn)
        if errors!="":
          ec.add(2, errors)
          errFlag=True
        else:
          errFlag=False

        sizeAdj+=self.getDirectorySize(j)

        rc=files.insertFileOrFolder(fn, size, sizeAdj, errFlag)
        ec.add(rc, fn)
        wx.Yield()
    self.fillListCtrl(self.list_panel1.list_ctrl, 1)
    ec.show()
    wx.EndBusyCursor()
    wx.Yield()

  # ###########################################################
  # Wie _getFileSize() - jedoch mit Fehlermeldungs-Popup.
  def getFileSize(self, fileOrFolder):
    s1, s2, errors=self._getFileSize(fileOrFolder)
    if errors!="":
      if len(errors)>1000:
        wx.MessageBox("Unable to access:"+errors[:1000], "Error", wx.OK|wx.ICON_ERROR)
      else:
        wx.MessageBox("Unable to access:"+errors, "Error", wx.OK|wx.ICON_ERROR)
    return(s1, s2)
  
  # ###########################################################
  # Liefert die Größe der Datei oder des Ordners "fileOrFolder"
  # als Tupel (Größe, auf Blocksize aufgerundete Größe).
  # Für einen Ordner wird die Größe aller enthaltenen Dateien
  # und Unterordner geliefert.
  # Nicht berücksichtigt wird die Größe im Directory von
  # "fileOrFolder" selbst.
  def _getFileSize(self, fileOrFolder, errors=""):
    fileSize=fileSizeAdj=0
    if ignore_symlinks_g==True and os.path.islink(fileOrFolder)==True:
      #print "link:", fileOrFolder#, os.path.getsize(fileOrFolder)
      pass
    elif os.path.isfile(fileOrFolder)==True:
      # -----------------------------------------
      # ----------------- Datei -----------------
      fileSize=os.path.getsize(fileOrFolder)
      if fileSize==0:                 # auch 0-Byte-Dateien...
        fileSizeAdj+=self.blockSize   # ...belegen einen Block
      else:
        fileSizeAdj=self.__adjustToBlockSize(fileSize)

      if self.addblock&1==1:                            # JolietRR  genisoimage -r -J
        pass
      if self.addblock&2==2:                            # UDF(1.02) genisoimage -udf
        fileSizeAdj+=self.blockSize
      if self.addblock&4==4:                            # UDF(2.01) mkudffs
        if fileSize>1832:                               # bei Dateien größer als 1832 Byte...
          fileSizeAdj+=self.blockSize                   # muss ein zusätzlicher Block reserviert werden
    elif os.path.isdir(fileOrFolder)==True:
      # -----------------------------------------
      # -------------- Verzeichnis --------------
      fileSizeAdj+=self.blockSize

      if self.addblock&1==1:                            # JolietRR  genisoimage -r -J
        fileSizeAdj+=self.blockSize
      if self.addblock&2==2:                            # UDF(1.02) genisoimage -udf
        fileSizeAdj+=(2*self.blockSize)

      try:
        fileOrFolderList=os.listdir(fileOrFolder)
      except:
        errors+="\n\t"+hlp.forceUTF8(fileOrFolder)
        return("error", "error", errors)

      dirsize=[0, 0, 0, 0, 0, 0] # 0:FAT32, 1:ISO9660, 2:Joliet(long), 3:Rock Ridge, 4:UDF1.02, 5:UDF2.01
      len_fofl=len(fileOrFolderList)
      for fileOrFolderSub in fileOrFolderList:  # Platzbedarf im Directory für Verzeichnis-Inhalt ermitteln
        try:
          fullname=os.path.join(fileOrFolder, fileOrFolderSub)
        except:
          # der Fehler wird weiter unten an "errors" übergeben
          continue
        isdir=os.path.isdir(fullname)
        dirsize_cur=self.getDirectorySizeV21(fileOrFolderSub, isdir, len_fofl)
        for i in range(len(dirsize)):
          dirsize[i]+=dirsize_cur[i]
      #print "dirsize={0:10} anzFiles={1:5} dir=".format(dirsize, len(fileOrFolderList)), fileOrFolder

      for i in range(len(dirsize)):
        if dirsize[i]>self.blockSize:
          fileSizeAdj+=self.__adjustToBlockSize(dirsize[i]-self.blockSize)
          if i==5 and self.addblock&4==4: # bei UDF(2.01)...
            fileSizeAdj+=self.blockSize   # nach dem ersten zusätzlichen Block, gleich noch einen weiteren reservieren

      for fileOrFolderSub in fileOrFolderList:
        try:
          fileOrFolderFullPath=os.path.join(fileOrFolder, fileOrFolderSub)
        except:
          errors+="\n\t"+hlp.forceUTF8(fileOrFolder)+"/"+hlp.forceUTF8(fileOrFolderSub)
          continue
        curSize, curSizeAdj, errors=self._getFileSize(fileOrFolderFullPath, errors)
        if type(curSize) in (int, long):    fileSize+=curSize
        if type(curSizeAdj) in (int, long): fileSizeAdj+=curSizeAdj
    else:
      errors+="\n\t"+hlp.forceUTF8(fileOrFolder)
    return(fileSize, fileSizeAdj, errors)

  # ###########################################################
  # Liefert den Platzbedarf im Directory für einen Namen
  def getDirectorySizeV21(self, fileOrFolderName, isdir, filesInDir=0):
    add=[0, 0, 0, 0, 0, 0] # 0:FAT32, 1:ISO9660, 2:Joliet(long), 3:Rock Ridge, 4:UDF1.02, 5:UDF2.01
    len_nam=len(fileOrFolderName)
    if self.addblock==0:        # FAT32
      add[0]+=self.__adjustToBlockSize(self.roundUp(len_nam*2.5+32), 32)
    else:
      if self.addblock&1==1:    # JolietRR  genisoimage -r -J
        if isdir==True:
          if len_nam<103:         # Joliet Verzeichnis
            add[2]+=len_nam*2+40
          else:
            add[2]+=250
        else:
          if len_nam<97:          # Joliet Datei
            add[2]+=len_nam*2+39
          else:
            add[2]+=251

        if len_nam<85:          # Rock Ridge
          add[3]+=len_nam+135
        else:
          add[3]+=self.blockSize

      if self.addblock&2==2:    # UDF(1.02) genisoimage -udf
        if not self.addblock&1==1:  # wenn JolietRR nicht an ist, muss ISO9660 hinzugerechnet werden
          if isdir==True:
            add[1]+=44          # ISO9660 Verzeichnis
          else:
            add[1]+=47          # ISO9660 Datei
        add[4]+=len_nam+43      # UDF 1.02

      if self.addblock&4==4:    # UDF(2.01) mkudffs
        if filesInDir>100:
          add[5]+=len_nam+42
        else:
          add[5]+=len_nam+50
    return(add)

  # ###########################################################
  # Liefert den Platzbedarf im Directory für einen Namen
  def getDirectorySize(self, fileOrFolderName, filesInDir=0):
    add=0
    len_nam=len(fileOrFolderName)
    if self.addblock==0:        # FAT32
      add+=self.__adjustToBlockSize(self.roundUp(len_nam*2.5+32), 32)
    else:
      if self.addblock&1==1:    # JolietRR  genisoimage -r -J
        if len_nam<85:
          add+=len_nam*3+175
        else:
          add+=self.blockSize
      if self.addblock&2==2:    # UDF(1.02) genisoimage -udf
        if self.addblock&1==1:  # wenn JolietRR auch an ist, braucht ISO9660 nicht hinzugerechnet werden
          add+=len_nam+43
        else:
          add+=len_nam+90
      if self.addblock&4==4:    # UDF(2.01) mkudffs
        if filesInDir>100:
          add+=len_nam+42
        else:
          add+=len_nam+50
    return(add)

  # ###########################################################
  # Liefert "val" als aufgerundeten int (ohne "import math").
  def roundUp(self, val):
    if val>int(val):
      return(int(val)+1)
    return(int(val))

  # ###########################################################
  # Liefert den auf ein Vielfaches von "self.blockSize"
  # aufgerundeten Wert von "fileSize".
  def __adjustToBlockSize(self, fileSize, bs=0):
    if bs==0:           # in der Funktionsdeklaration will der Interpreter keine
      bs=self.blockSize # variable Vorbelegung a la "bs=self.blockSize" haben
    mod=fileSize%bs
    if mod==0:
      return(int(fileSize))
    return(int(fileSize+(bs-mod)))

  # ###########################################################
  # Kontextmenü in "self.list_panel1.list_ctrl" gewählt.
  def OnRightClick1(self, event):
    self.menue=wx.Menu()
    self.menue.Append(10,  'select all')
    self.menue.Append(100, 'move to destination list')
    self.menue.AppendSeparator()
    self.menue.Append(150, 'select sequences')
    self.menue.AppendSeparator()
    self.menue.Append(200, 'remove from list')
    self.menue.Append(210, 'remove all from list')

    self.Bind(wx.EVT_MENU, self.selectAllListCtrl1, id=10)
    self.Bind(wx.EVT_MENU, self.moveToListCtrl2, id=100)
    self.Bind(wx.EVT_MENU, self.selectSequences, id=150)
    self.Bind(wx.EVT_MENU, self.deleteFromListCtrl1, id=200)
    self.Bind(wx.EVT_MENU, self.deleteAllFromListCtrl1, id=210)

    self.PopupMenu(self.menue)

  # ###########################################################
  # Markiert bzw. selektiert alle Zeilen in "self.list_panel1.list_ctrl"
  def selectAllListCtrl1(self, event):
    for i in range(self.list_panel1.list_ctrl.GetItemCount()):
      self.list_panel1.list_ctrl.Select(i)

  # ###########################################################
  # Verschiebt die selektierten Sätze aus "self.list_panel1.list_ctrl.data"
  # nach "self.list_panel2.list_ctrl.data" ( -> ).
  def moveToListCtrl2(self, event):
    ec=insertErrorCollector(self)
    wx.BeginBusyCursor()
    wx.Yield()
    moveLst=self.getSelectedItems(self.list_panel1.list_ctrl)
    topItem1=self.list_panel1.list_ctrl.GetTopItem()
    topItem2=self.list_panel2.list_ctrl.GetTopItem()
    for i in moveLst:
      idx=self.list_panel1.list_ctrl.GetItemData(i)
      data=self.list_panel1.list_ctrl.data.getFileOrFolder(idx)
      rc=self.list_panel2.list_ctrl.data.insertFileOrFolder(data.fullname, data.size, data.sizeAdj, data.hasErrors)
      if rc>0:
        ec.add(rc, data.fullname)
      self.list_panel1.list_ctrl.data.removeByIndex(idx)
    self.fillListCtrl(self.list_panel1.list_ctrl, 1)
    self.fillListCtrl(self.list_panel2.list_ctrl, 2)
    self.restoreSort(self.list_panel1, topItem1)
    self.restoreSort(self.list_panel2, topItem2)
    ec.show()
    wx.EndBusyCursor()
    wx.Yield()

  # ###########################################################
  #
  def selectSequences(self, event):
    selLst=self.getSelectedItems(self.list_panel1.list_ctrl)
    for i in selLst:
      self.list_panel1.list_ctrl.Select(i, 0) # alles deselektieren

    lst=[]
    for i in range(self.list_panel1.list_ctrl.GetItemCount()):
      idx=self.list_panel1.list_ctrl.GetItemData(i)
      lst.append(self.list_panel1.list_ctrl.data.getFileOrFolder(idx).filename)

    cf=ConnectedFiles.ConnectedFiles(lst)
    cfl=cf.getConnectedFiles()
    for fn in cfl:
      #print fn
      for i in range(self.list_panel1.list_ctrl.GetItemCount()):
        idx=self.list_panel1.list_ctrl.GetItemData(i)
        if fn==self.list_panel1.list_ctrl.data.getFileOrFolder(idx).filename:
          #print self.list_panel1.list_ctrl.data.getFileOrFolder(idx).filename, i, idx
          self.list_panel1.list_ctrl.Select(i)

  # ###########################################################
  # Löscht die selektierten Sätze aus "self.list_panel1.list_ctrl.data"
  # und stellt danach das ListCtrl entspr. dar.
  def deleteFromListCtrl1(self, event):
    delLst=self.getSelectedItems(self.list_panel1.list_ctrl)
    topItem1=self.list_panel1.list_ctrl.GetTopItem()
    for i in delLst:
      idx=self.list_panel1.list_ctrl.GetItemData(i)
      self.list_panel1.list_ctrl.data.removeByIndex(idx)
    self.fillListCtrl(self.list_panel1.list_ctrl, 1)
    self.restoreSort(self.list_panel1, topItem1)

  # ###########################################################
  # Löscht alles Sätze aus "self.list_panel1.list_ctrl.data".
  def deleteAllFromListCtrl1(self, event):
    self.list_panel1.list_ctrl.data.clear()
    self.list_panel1.list_ctrl.DeleteAllItems()
    self.__updateSum(self.list_panel1.list_ctrl, 1)
    self.base_profile.SetValue("")

  # ###########################################################
  # Kontextmenü in "self.list_panel2.list_ctrl" gewählt.
  def OnRightClick2(self, event):
    self.menue=wx.Menu()
    self.menue.Append(10,  'select all')
    self.menue.Append(100, 'move back to source list')
    self.menue.AppendSeparator()
    self.menue.Append(200, 'remove from list')
    self.menue.Append(210, 'remove all from list')

    self.Bind(wx.EVT_MENU, self.selectAllListCtrl2, id=10)
    self.Bind(wx.EVT_MENU, self.moveToListCtrl1, id=100)
    self.Bind(wx.EVT_MENU, self.deleteFromListCtrl2, id=200)
    self.Bind(wx.EVT_MENU, self.deleteAllFromListCtrl2, id=210)

    self.PopupMenu(self.menue)

  # ###########################################################
  # Markiert bzw. selektiert alle Zeilen in "self.list_panel2.list_ctrl"
  def selectAllListCtrl2(self, event):
    for i in range(self.list_panel2.list_ctrl.GetItemCount()):
      self.list_panel2.list_ctrl.Select(i)

  # ###########################################################
  # Verschiebt die selektierten Sätze aus "self.list_panel2.list_ctrl.data"
  # nach "self.list_panel1.list_ctrl.data" ( <- ).
  def moveToListCtrl1(self, event):
    ec=insertErrorCollector(self)
    wx.BeginBusyCursor()
    wx.Yield()
    moveLst=self.getSelectedItems(self.list_panel2.list_ctrl)
    topItem1=self.list_panel1.list_ctrl.GetTopItem()
    topItem2=self.list_panel2.list_ctrl.GetTopItem()
    for i in moveLst:
      idx=self.list_panel2.list_ctrl.GetItemData(i)
      data=self.list_panel2.list_ctrl.data.getFileOrFolder(idx)
      rc=self.list_panel1.list_ctrl.data.insertFileOrFolder(data.fullname, data.size, data.sizeAdj, data.hasErrors)
      if rc>0:
        ec.add(rc, data.fullname)
      self.list_panel2.list_ctrl.data.removeByIndex(idx)
    self.fillListCtrl(self.list_panel1.list_ctrl, 1)
    self.fillListCtrl(self.list_panel2.list_ctrl, 2)
    self.restoreSort(self.list_panel1, topItem1)
    self.restoreSort(self.list_panel2, topItem2)
    ec.show()
    wx.EndBusyCursor()
    wx.Yield()

  # ###########################################################
  # Löscht die selektierten Sätze aus "self.list_panel2.list_ctrl.data"
  # und stellt danach das ListCtrl entspr. dar.
  def deleteFromListCtrl2(self, event):
    delLst=self.getSelectedItems(self.list_panel2.list_ctrl)
    topItem2=self.list_panel2.list_ctrl.GetTopItem()
    for i in delLst:
      idx=self.list_panel2.list_ctrl.GetItemData(i)
      self.list_panel2.list_ctrl.data.removeByIndex(idx)
    self.fillListCtrl(self.list_panel2.list_ctrl, 2)
    self.restoreSort(self.list_panel2, topItem2)

  # ###########################################################
  # Löscht alles Sätze aus "self.list_panel2.list_ctrl.data".
  def deleteAllFromListCtrl2(self, event):
    self.list_panel2.list_ctrl.data.clear()
    self.list_panel2.list_ctrl.DeleteAllItems()
    self.__updateSum(self.list_panel2.list_ctrl, 2)
    self.base_profile.SetValue("")

  # ###########################################################
  # Liefert eine Liste mit den Indices der selektierten Sätze
  # in "ctrl".
  def getSelectedItems(self, ctrl):
    lst=[]
    idx=ctrl.GetFirstSelected()
    while idx!=-1:
      lst.append(idx)
      idx=ctrl.GetNextSelected(idx)
    return(lst)



if __name__=='__main__':
  app=wx.App()
  pos, size=cfgfile.getWindowSize()
  frame=FillBD2Frame(pos, size)
  frame.Show()
  app.MainLoop()

