#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import os

import Database

import Helpers as hlp

#class SetupDialog(wx.Dialog):
#class AddOrEditBaseProfile(wx.Dialog):
#class AddOrEditDestProfile(wx.Dialog):

# ###########################################################
# Ein Setup-Dialog-Fenster zum Einstellen von
# - Basis-Pfad-Profilen (mit Profilname, Kommentar und
#   Basis-Pfaden
# - der maximalen Rechendauer [Sek]
# - Ziel-Datenträger-Profil (mit Profilname, Kommentar, 
#   Datenträger-Größe, Block-Größe und Zielverzeichnis).
class SetupDialog(wx.Dialog):
  def __init__(self, parent, calcTime):
    wx.Dialog.__init__(self, parent, wx.ID_ANY, "Setup", style=wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER)
    self.parent=parent
    self.calcTimeOld=calcTime
    self.db=Database.Database()
    self.InitUI()
    self.Centre()

  # ###########################################################
  # Fenster-Inhalt definieren
  def InitUI(self):
    vsizer=wx.BoxSizer(wx.VERTICAL)

    txt=wx.StaticText(self, label="Source Profiles")
    vsizer.Add(txt, 0, wx.TOP|wx.LEFT, 4)
    self.basePathList=wx.ListCtrl(self, size=(900, 150), style=wx.LC_REPORT)
    self.basePathList.InsertColumn(0, "Profilename", width=100)
    self.basePathList.InsertColumn(1, "Comment", width=230)
    self.basePathList.InsertColumn(2, "hid", width=30)
    self.basePathList.InsertColumn(3, "Path-List", width=550)
    vsizer.Add(self.basePathList, 1, wx.ALL|wx.EXPAND, 4)

    txt=wx.StaticText(self, label="Target Profiles")
    vsizer.Add(txt, 0, wx.TOP|wx.LEFT, 4)
    self.destPathList=wx.ListCtrl(self, size=(900, 150), style=wx.LC_REPORT)
    self.destPathList.InsertColumn(0, "Profilename",                width=150)
    self.destPathList.InsertColumn(1, "Comment",                    width=230)
    self.destPathList.InsertColumn(2, "Size",       wx.LIST_FORMAT_RIGHT, 150)
    self.destPathList.InsertColumn(3, "BlockSize",  wx.LIST_FORMAT_RIGHT, 100)
    self.destPathList.InsertColumn(4, "add",        wx.LIST_FORMAT_RIGHT,  30)
    self.destPathList.InsertColumn(5, "Folder",                     width=200)
    self.destPathList.InsertColumn(6, "final",                      width= 50)
    vsizer.Add(self.destPathList, 1, wx.ALL|wx.EXPAND, 4)

    hsizer=wx.BoxSizer(wx.HORIZONTAL)
    txt=wx.StaticText(self, label="max. calculation time [sec]:")
    hsizer.Add(txt, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 4)
    self.calcTime=wx.SpinCtrl(self, min=1, max=60, size=(40, -1))
    self.calcTime.SetValue(self.calcTimeOld)
    hsizer.Add(self.calcTime, 1, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 4)
    hsizer.AddStretchSpacer(2)
    ok=wx.Button(self, label="Ok")
    hsizer.Add(ok, 0, wx.ALIGN_RIGHT, 4)
    vsizer.Add(hsizer, 0, wx.RIGHT|wx.BOTTOM|wx.ALIGN_RIGHT, 4)

    self.basePathList.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick_base)
    self.destPathList.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick_dest)
    ok.Bind(wx.EVT_BUTTON, self.okBut)

    idx=0
    for i in self.db.getBaseProfiles():
      self.insertInBasePathList(idx, i[0], i[1], i[2], i[3])
      idx+=1

    idx=0
    for i in self.db.getDestProfiles():
      self.insertInDestPathList(idx, i[0], i[1], i[2], i[3], i[4], i[5], i[6])
      idx+=1

    self.SetSizer(vsizer)
    vsizer.Fit(self)
    ok.SetFocus()

  # ###########################################################
  # Fügt einen Satz in "basePathList" ein.
  def insertInBasePathList(self, index, name, comment, inclHidden, folderList):
    i=self.basePathList.InsertStringItem(index, name)
    self.basePathList.SetStringItem(i, 1, comment)
    self.basePathList.SetStringItem(i, 2, str(inclHidden))
    self.basePathList.SetStringItem(i, 3, self.listToString(folderList))
    self.basePathList.SetItemData(i, index)

  # ###########################################################
  # Liefert zu einer Liste eine etwas hübschere Repäsentation,
  # als str(lst) es täte.
  def listToString(self, lst):
    s=""
    for l in lst:
      s+=', "'+l+'"'
    return(s[2:])

  # ###########################################################
  # Liefert den Satz aus basePathList zu item.
  def getFromBasePath(self, item):
    name=self.basePathList.GetItem(item, 0).GetText()
    data=self.db.getBaseProfiles(name)
    return(data)

  # ###########################################################
  # Liefert den Satz aus destPathList zu item.
  def getFromDestPath(self, item):
    name=self.destPathList.GetItem(item, 0).GetText()
    data=self.db.getDestProfiles(name)
    return(data)

  # ###########################################################
  # Fügt einen Satz in "destPathList" ein.
  def insertInDestPathList(self, index, name, comment, size, blocksize, addblock, folder, final):
    i=self.destPathList.InsertStringItem(index, name)
    self.destPathList.SetStringItem(i, 1, comment)
    self.destPathList.SetStringItem(i, 2, hlp.intToStringWithCommas(size))
    self.destPathList.SetStringItem(i, 3, hlp.intToStringWithCommas(blocksize))
    self.destPathList.SetStringItem(i, 4, str(addblock))
    self.destPathList.SetStringItem(i, 5, folder)
    if final==0:
      self.destPathList.SetStringItem(i, 6, "no")
    else:
      self.destPathList.SetStringItem(i, 6, "yes")
    self.destPathList.SetItemData(i, index)
    
  # ###########################################################
  # Ok-Button wurde gewählt.
  def okBut(self, event):
    self.EndModal(wx.ID_OK)

  # ###########################################################
  # Liefert die eingestellte Maximal-Rechendauer als Integer.
  def getData(self):
    return(self.calcTime.GetValue())

  # ###########################################################
  # Menü für "basePathList".
  def OnRightClick_base(self, event):
    self.menue=wx.Menu()
    self.menue.Append(100, 'add new profile')
    self.menue.Append(200, 'edit profile')
    self.menue.Append(300, 'remove profile')

    self.Bind(wx.EVT_MENU, self.add_base,     id=100)
    self.Bind(wx.EVT_MENU, self.edit_base,    id=200)
    self.Bind(wx.EVT_MENU, self.remove_base,  id=300)
    self.PopupMenu(self.menue)

  # ###########################################################
  # Fügt einen neuen Satz in "basePathList" ein.
  def add_base(self, event):
    dlg=AddOrEditBaseProfile(self, [], self.db.getBaseProfileNames())
    if dlg.ShowModal()!=wx.ID_OK:
      dlg.Destroy()
      return
    data=dlg.getData()
    dlg.Destroy()
    self.insertInBasePathList(0, data[0], data[1], data[2], data[3])
    self.db.insertOrUpdateBase(data[0], data[1], data[2], data[3])

  # ###########################################################
  # Ändert den selektierten Satz aus "basePathList".
  def edit_base(self, event):
    it=self.basePathList.GetFirstSelected()
    while it>-1: # solange es selektierte Sätze gibt
      data=self.getFromBasePath(it)
      dlg=AddOrEditBaseProfile(self, data[0])
      if dlg.ShowModal()!=wx.ID_OK:
        dlg.Destroy()
      else:
        data=dlg.getData()
        dlg.Destroy()
        self.basePathList.SetStringItem(it, 0, data[0])
        self.basePathList.SetStringItem(it, 1, data[1])
        self.basePathList.SetStringItem(it, 2, str(data[2]))
        self.basePathList.SetStringItem(it, 3, self.listToString(data[3]))
        self.db.insertOrUpdateBase(data[0], data[1], data[2], data[3])
      it=self.basePathList.GetNextSelected(it)
    
  # ###########################################################
  # Löscht die selektierten Sätze in "basePathList".
  def remove_base(self, event):
    it=self.basePathList.GetFirstSelected()
    while it>-1: # solange mind. ein Satz selektiert ist
      name=self.basePathList.GetItem(it, 0).GetText()
      self.db.deleteBase(name)
      self.basePathList.DeleteItem(it)
      it=self.basePathList.GetFirstSelected()

  # ###########################################################
  # Menü für "destPathList".
  def OnRightClick_dest(self, event):
    self.menue=wx.Menu()
    self.menue.Append(100, 'add new profile')
    self.menue.Append(200, 'edit profile')
    self.menue.Append(300, 'remove profile')

    self.Bind(wx.EVT_MENU, self.add_dest,     id=100)
    self.Bind(wx.EVT_MENU, self.edit_dest,    id=200)
    self.Bind(wx.EVT_MENU, self.remove_dest,  id=300)
    self.PopupMenu(self.menue)

  # ###########################################################
  # Fügt einen neuen Satz in "destPathList" ein.
  def add_dest(self, event):
    dlg=AddOrEditDestProfile(self, [], self.db.getDestProfileNames())
    if dlg.ShowModal()!=wx.ID_OK:
      dlg.Destroy()
      return
    data=dlg.getData()
    dlg.Destroy()
    self.insertInDestPathList(0, data[0], data[1], data[2], data[3], data[4], data[5], data[6])
    self.db.insertOrUpdateDest(data[0], data[1], data[2], data[3], data[4], data[5], data[6])

  # ###########################################################
  # Ändert den selektierten Satz aus "destPathList".
  def edit_dest(self, event):
    it=self.destPathList.GetFirstSelected()
    while it>-1: # solange es selektierte Sätze gibt
      data=self.getFromDestPath(it)
      dlg=AddOrEditDestProfile(self, data[0])
      if dlg.ShowModal()!=wx.ID_OK:
        dlg.Destroy()
      else:
        data=dlg.getData()
        dlg.Destroy()
        self.destPathList.SetStringItem(it, 0, data[0])
        self.destPathList.SetStringItem(it, 1, data[1])
        self.destPathList.SetStringItem(it, 2, hlp.intToStringWithCommas(data[2]))
        self.destPathList.SetStringItem(it, 3, hlp.intToStringWithCommas(data[3]))
        self.destPathList.SetStringItem(it, 4, str(data[4]))
        self.destPathList.SetStringItem(it, 5, data[5])
        if data[6]==0:
          self.destPathList.SetStringItem(it, 6, "no")
        else:
          self.destPathList.SetStringItem(it, 6, "yes")
        self.db.insertOrUpdateDest(data[0], data[1], data[2], data[3], data[4], data[5], data[6])
      it=self.destPathList.GetNextSelected(it)

  # ###########################################################
  # Löscht die selektierten Sätze in "basePathList".
  def remove_dest(self, event):
    it=self.destPathList.GetFirstSelected()
    while it>-1: # solange mind. ein Satz selektiert ist
      name=self.destPathList.GetItem(it, 0).GetText()
      self.db.deleteDest(name)
      self.destPathList.DeleteItem(it)
      it=self.destPathList.GetFirstSelected()





# ###########################################################
# Ein Dialog-Fenter zum Bearbeiten eines SourceProfiles.
class AddOrEditBaseProfile(wx.Dialog):
  def __init__(self, parent, data=[], existingNames=[]):
    wx.Dialog.__init__(self, parent, wx.ID_ANY, "Source Profile", \
                        style=wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER)
    self.data=data
    self.existingNames=existingNames
    self.InitUI()
    self.Centre()

  # ###########################################################
  # Fenster-Inhalt definieren
  def InitUI(self):
    txt1=wx.StaticText(self, label="Profilename:")
    self.name=wx.TextCtrl(self, wx.ID_ANY, "", size=(250, -1))
    txt2=wx.StaticText(self, label="Comment:")
    self.comment=wx.TextCtrl(self, wx.ID_ANY, "", size=(250, -1))
    txt3=wx.StaticText(self, label="Path List:")
    self.pathList=wx.ListBox(self, wx.ID_ANY, size=(250, 200))
    addPth=wx.Button(self, wx.ID_ANY, "&+ Add")
    delPth=wx.Button(self, wx.ID_ANY, "&- Del")
    self.inclHidden=wx.CheckBox(self, wx.ID_ANY, "include hidden files or folders")
    ok=wx.Button(self, wx.ID_OK, "&Ok")
    cancel=wx.Button(self, wx.ID_CANCEL, "&Cancel")

    addPth.Bind(wx.EVT_BUTTON, self.addPthBut)
    delPth.Bind(wx.EVT_BUTTON, self.delPthBut)
    ok.Bind(wx.EVT_BUTTON, self.okBut)
    cancel.Bind(wx.EVT_BUTTON, self.cancelBut)

    sizer=wx.GridBagSizer(4, 4)
    sl=wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
    st=wx.RIGHT
    sizer.Add(txt1,           (0, 0), (1, 1), sl|wx.TOP,            4)
    sizer.Add(self.name,      (0, 1), (1, 1), st|wx.TOP|wx.EXPAND,  4)
    sizer.Add(txt2,           (1, 0), (1, 1), sl,                   4)
    sizer.Add(self.comment,   (1, 1), (1, 1), st|wx.EXPAND,         4)
    sizer.Add(txt3,           (2, 0), (1, 1), wx.LEFT|wx.ALIGN_RIGHT|wx.ALIGN_TOP, 4)
    sizer.Add(self.pathList,  (2, 1), (1, 1), st|wx.EXPAND,         4)
    sizer.Add(self.inclHidden,(3, 1), (1, 1), st,                   4)
    sizer.AddGrowableCol(1, 1)
    sizer.AddGrowableRow(2, 1)

    vsizer=wx.BoxSizer(wx.VERTICAL)
    vsizer.Add(addPth, 0, wx.BOTTOM, 4)
    vsizer.Add(delPth, 0, wx.TOP, 4)
    sizer.Add(vsizer,         (2, 2), (1, 1), st, 4)

    hsizer=wx.BoxSizer(wx.HORIZONTAL)
    hsizer.Add(ok,      0, wx.RIGHT, 4)
    hsizer.Add(cancel,  0, wx.LEFT, 4)
    sizer.Add(hsizer,         (4, 1), (1, 3), wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT, 4)

    if self.data!=[]:
      self.name.SetValue(self.data[0])
      self.name.Disable() # der Key darf nicht verändert werden
      self.comment.SetValue(self.data[1])
      self.inclHidden.SetValue(self.data[2])
      self.pathList.InsertItems(self.data[3], 0)
      ok.SetFocus()
    else:
      self.name.SetFocus()

    self.SetSizer(sizer)
    sizer.Fit(self)
    self.startPath=""

  # ###########################################################
  # Fügt einen neuen Ordner zu "pathList" hinzu.
  def addPthBut(self, event):
    dlg=wx.DirDialog(self, "Select Folder", self.startPath)
    if dlg.ShowModal()!=wx.ID_OK:
      dlg.Destroy()
      return
    pth=dlg.GetPath()
    dlg.Destroy()

    if len(pth)==0: # ==0 kann vorkommen, wenn...
      return        # ein Ordner mit illegalen Zeichen gewählt wurde

    if os.access(pth, os.F_OK|os.R_OK)!=True:
      wx.MessageBox("Unable to access :\n\t"+pth, "Error", wx.OK | wx.ICON_ERROR)
      return

    p=self.pathList.FindString(pth) # "pth" in ListBox suchen
    if p==wx.NOT_FOUND:
      self.pathList.InsertItems([pth], 0)
    else:
      self.pathList.Select(p)
    self.startPath=os.path.dirname(pth)

  # ###########################################################
  # Löscht den selektierten Ordner aus "pathList". Es kann und
  # darf immer nur ein Ordner selektiert sein.
  def delPthBut(self, event):
    pl=self.pathList.GetSelections()
    if len(pl)>0:
      self.pathList.Delete(pl[0])

  # ###########################################################
  # Liefert die Daten des Dialoges.
  def getData(self):
    return( ( self.name.GetValue(),
              self.comment.GetValue(),
              int(self.inclHidden.GetValue()),
              self.pathList.GetItems()
            )
          )

  # ###########################################################
  # Cancel-Button wurde gewählt.
  def cancelBut(self, event):
    self.EndModal(wx.ID_CANCEL)

  # ###########################################################
  # Ok-Button wurde gewählt.
  def okBut(self, event):
    if self.name.GetValue()=="":
      wx.MessageBox("<Name> must have a value!", "Error", wx.OK)
      self.name.SetFocus()
      return
    if self.name.GetValue() in self.existingNames:
      wx.MessageBox('the <Name> "'+self.name.GetValue()+'" already exists!', "Error", wx.OK)
      self.name.SetFocus()
      return

    self.EndModal(wx.ID_OK)




# ###########################################################
# Ein Dialog-Fenter zum Bearbeiten eines DestinationProfiles.
class AddOrEditDestProfile(wx.Dialog):
  def __init__(self, parent, data=[], existingNames=[]):
    wx.Dialog.__init__(self, parent, wx.ID_ANY, "Target Profile", \
                        style=wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER)
    self.data=data
    self.existingNames=existingNames
    self.InitUI()
    self.Centre()

  # ###########################################################
  # Fenster-Inhalt definieren
  def InitUI(self):
    txt1=wx.StaticText(self, label="Profilename:")
    self.name=wx.TextCtrl(self, wx.ID_ANY, "", size=(250, -1))
    txt2=wx.StaticText(self, label="Comment:")
    self.comment=wx.TextCtrl(self, wx.ID_ANY, "", size=(250, -1))
    txt3=wx.StaticText(self, label="Size:")
    self.size=wx.TextCtrl(self, wx.ID_ANY, "", size=(150, -1))
    txt4=wx.StaticText(self, label="Blocksize:")
    self.blocksize=wx.TextCtrl(self, wx.ID_ANY, "", size=(100, -1))
    self.addBlock1=wx.CheckBox(self, wx.ID_ANY, "Joliet + Rock Ridge (genisoimage)")
    self.addBlock2=wx.CheckBox(self, wx.ID_ANY, "UDF 1.02 (genisoimage)")
    self.addBlock3=wx.CheckBox(self, wx.ID_ANY, "UDF 2.01 (mkudffs)")

    sel=wx.Button(self, wx.ID_ANY, "Select &Folder", style=wx.BU_EXACTFIT)
    self.folder=wx.TextCtrl(self, wx.ID_ANY, "", size=(250, -1))
    self.final=wx.RadioBox(self, wx.ID_ANY, "<Folder> is the...", \
                choices=["starting point for the target folder", "target folder"], \
                style=wx.RA_SPECIFY_ROWS)
    ok=wx.Button(self, wx.ID_OK, "&Ok")
    cancel=wx.Button(self, wx.ID_CANCEL, "&Cancel")

    sel.Bind(wx.EVT_BUTTON, self.selBut)
    ok.Bind(wx.EVT_BUTTON, self.okBut)
    cancel.Bind(wx.EVT_BUTTON, self.cancelBut)
    self.addBlock1.Bind(wx.EVT_CHECKBOX, self.joliet)
    self.addBlock2.Bind(wx.EVT_CHECKBOX, self.udf102)
    self.addBlock3.Bind(wx.EVT_CHECKBOX, self.udf201)

    sizer=wx.GridBagSizer(4, 4)
    sl=wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
    st=wx.RIGHT
    sizer.Add(txt1,           (0, 0), (1, 1), sl|wx.TOP,            4)
    sizer.Add(self.name,      (0, 1), (1, 2), st|wx.TOP|wx.EXPAND,  4)
    sizer.Add(txt2,           (1, 0), (1, 1), sl,                   4)
    sizer.Add(self.comment,   (1, 1), (1, 2), st|wx.EXPAND,         4)
    sizer.Add(txt3,           (2, 0), (1, 1), sl,                   4)
    sizer.Add(self.size,      (2, 1), (1, 2), st,                   4)
    sizer.Add(txt4,           (3, 0), (1, 1), sl,                   4)
    sizer.Add(self.blocksize, (3, 1), (1, 1), st,                   4)
    sizer.Add(self.addBlock1, (4, 1), (1, 1), st,                   4)
    sizer.Add(self.addBlock2, (5, 1), (1, 1), st,                   4)
    sizer.Add(self.addBlock3, (6, 1), (1, 1), st,                   4)
    sizer.Add(sel,            (7, 0), (1, 1), sl,                   4)
    sizer.Add(self.folder,    (7, 1), (1, 2), st|wx.EXPAND,         4)
    sizer.Add(self.final,     (8, 1), (1, 2), st,                   4)
    sizer.AddGrowableCol(1, 1)

    hsizer=wx.BoxSizer(wx.HORIZONTAL)
    hsizer.Add(ok,      0, wx.RIGHT, 4)
    hsizer.Add(cancel,  0, wx.LEFT, 4)
    sizer.Add(hsizer,         (9, 1), (1, 2), wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT, 4)

    if self.data!=[]:
      self.name.SetValue(self.data[0])
      self.name.Disable()  # der Key darf nicht verändert werden
      self.comment.SetValue(self.data[1])
      self.size.SetValue(hlp.intToStringWithCommas(self.data[2]))
      self.blocksize.SetValue(hlp.intToStringWithCommas(self.data[3]))
      self.setAddBlock(self.data[4])
      self.folder.SetValue(self.data[5])
      self.final.SetSelection(self.data[6])
      ok.SetFocus()
    else:
      self.name.SetFocus()

    self.SetSizer(sizer)
    sizer.Fit(self)

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
  # Liefert die Daten des Dialoges.
  def getData(self):
    return( ( self.name.GetValue(),
              self.comment.GetValue(),
              hlp.stringWithCommasToInt(self.size.GetValue()),
              hlp.stringWithCommasToInt(self.blocksize.GetValue()),
              self.getAddBlock(),
              self.folder.GetValue(),
              self.final.GetSelection()
            )
          )

  # ###########################################################
  # "Select Folder"-Button wurde gewählt.
  def selBut(self, event):
    dlg=wx.DirDialog(self, "Target Folder", self.folder.GetValue())
    if dlg.ShowModal()!=wx.ID_OK:
      dlg.Destroy()
      return
    
    destPath=dlg.GetPath()
    dlg.Destroy()
    if os.access(destPath, os.F_OK|os.W_OK)==True:
      self.folder.SetValue(destPath)
    else:
      wx.MessageBox("Unable to access :\n\t"+destPath, "Error", wx.OK | wx.ICON_ERROR)

  # ###########################################################
  # Ok-Button wurde gewählt.
  def okBut(self, event):
    if self.name.GetValue()=="":
      wx.MessageBox("<Name> must have a value!", "Error", wx.OK)
      self.name.SetFocus()
      return
    if self.name.GetValue() in self.existingNames:
      wx.MessageBox('the <Name> "'+self.name.GetValue()+'" already exists!', "Error", wx.OK)
      self.name.SetFocus()
      return
    destPath=self.folder.GetValue()
    if destPath=="":
      wx.MessageBox("Missing target folder", "Error", wx.OK | wx.ICON_ERROR)
      self.folder.SetFocus()
      return
    if os.access(destPath, os.F_OK|os.W_OK)!=True:
      wx.MessageBox("Unable to access :\n\t"+destPath, "Error", wx.OK | wx.ICON_ERROR)
      self.folder.SetFocus()
      return
    self.EndModal(wx.ID_OK)

  # ###########################################################
  # Cancel-Button wurde gewählt.
  def cancelBut(self, event):
    self.EndModal(wx.ID_CANCEL)

