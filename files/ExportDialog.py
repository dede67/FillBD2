#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import os
import time
import select
from collections import OrderedDict
import subprocess
import tempfile

import ConfigFile as cfgfile
import Helpers as hlp

#class ExportDialog(wx.Dialog):
#class ExecutionProgressDialog(wx.Dialog):
#class VolIdImageNameDialog(wx.Dialog):

DEBUG_FS=False
#DEBUG_FS=True

# ###########################################################
# Der Dialog zur Auswahl der Export-Methode (cp/mv/clipboard)
# und Start des Exports über ExecutionProgressDialog().
class ExportDialog(wx.Dialog):
  def __init__(self, parent, targetFolder, fileDict, addblock):
    wx.Dialog.__init__(self, parent, wx.ID_ANY, "Export", \
                        style=wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER)
    self.parent=parent
    self.targetFolder=targetFolder
    self.fileDict=fileDict
    self.addblock=addblock
    self.InitUI()
    self.Centre()

  # ###########################################################
  # Fenster-Inhalt definieren
  def InitUI(self):
    txt1=wx.StaticText(self, label="Target Folder:")
    self.folder=wx.TextCtrl(self, wx.ID_ANY, "", size=(250, -1), style=wx.TE_READONLY)
    self.folder.SetValue(self.targetFolder)
    txt2=wx.StaticText(self, label="Number of Files:")
    self.fileCount=wx.TextCtrl(self, wx.ID_ANY, str(len(self.fileDict)), \
                                size=(50, -1), style=wx.TE_READONLY)
    gip=self.getGenisoimageParm()
    self.todo=wx.RadioBox(self, wx.ID_ANY, "select", \
                choices=[ "copy files to target folder", \
                          "move files to target folder", \
                          "genisoimage"+gip], \
                style=wx.RA_SPECIFY_ROWS)

    self.toClipboard=wx.CheckBox(self, wx.ID_ANY, "copy commands to clipboard")
    ok=wx.Button(self, wx.ID_OK, "&Ok")
    cancel=wx.Button(self, wx.ID_CANCEL, "&Cancel")

    if gip=="":                       # wenn keine Parameter für genisoimage angegeben wurden
      self.todo.EnableItem(2, False)  # ...dann deaktivieren
    else:
      self.todo.SetSelection(2)
      self.toClipboard.Disable()

    self.todo.Bind(wx.EVT_RADIOBOX, self.todoChanged)
    ok.Bind(wx.EVT_BUTTON, self.okBut)
    cancel.Bind(wx.EVT_BUTTON, self.cancelBut)

    sizer=wx.GridBagSizer(4, 4)
    sl=wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
    st=wx.RIGHT
    sizer.Add(txt1,             (0, 0), (1, 1), sl|wx.TOP,                  4)
    sizer.Add(self.folder,      (0, 1), (1, 1), st|wx.TOP|wx.EXPAND,        4)
    sizer.Add(txt2,             (1, 0), (1, 1), sl|wx.TOP,                  4)
    sizer.Add(self.fileCount,   (1, 1), (1, 1), st|wx.ALIGN_LEFT,           4)
    sizer.Add(self.todo,        (2, 1), (1, 1), st|wx.ALIGN_LEFT|wx.EXPAND, 4)
    sizer.Add(self.toClipboard, (3, 1), (1, 1), st|wx.ALIGN_LEFT,           4)
    sizer.AddGrowableCol(1, 1)

    hsizer=wx.BoxSizer(wx.HORIZONTAL)
    hsizer.Add(ok,      0, wx.RIGHT, 4)
    hsizer.Add(cancel,  0, wx.LEFT, 4)
    sizer.Add(hsizer,           (4, 1), (1, 1), wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT, 4)

    if self.targetFolder=="" or len(self.fileDict)==0:
      ok.Disable()

    self.SetSizer(sizer)
    sizer.Fit(self)
    cancel.SetFocus()

#    for key, data in self.fileDict.items():
#      print "\n", key
#      print "  foldername", data.foldername
#      print "  filename  ", data.filename
#      print "  sizeAdj   ", data.sizeAdj
#      print "  isFolder  ", data.isFolder
#      print "  isFile    ", data.isFile
#      print "  isSymLink ", data.isSymLink

  # ###########################################################
  # Wird aufgerufen, wenn in der Radio-Box geändert wurde.
  def todoChanged(self, event):
    if self.todo.GetSelection()==2: # wenn genisoimage gewählt
      self.toClipboard.SetValue(False)
      self.toClipboard.Disable()
      return
    self.toClipboard.Enable()

  # ###########################################################
  # Kopiert "text" ins Clipboard.
  def copyToClipboard(self, text):
    if wx.TheClipboard.Open():
      do=wx.TextDataObject()
      do.SetText(text)
      wx.TheClipboard.SetData(do)
      wx.TheClipboard.Close()
    else:
      wx.MessageBox("Unable to open clipboard!", "Error", wx.OK|wx.ICON_ERROR)

  # ###########################################################
  # Liefert einen String mit den Parametern für genisoimage
  # gemäß Setting in "self.addblock".
  def getGenisoimageParm(self):
    rc=""
    if self.addblock!=None:
      if (self.addblock&1)==1: rc+=" -r -J -joliet-long"
      if (self.addblock&2)==2: rc+=" -udf -D"
    return(rc)

  # ###########################################################
  # Ok-Button wurde gewählt.
  def okBut(self, event):
    sel=self.todo.GetSelection()

    if self.toClipboard.GetValue()==True:
      if sel==0:  cmd='cp -rp "%s" "%s"\n'
      if sel==1:  cmd='mv "%s" "%s"\n'
      txt=""
      for fn in sorted(self.fileDict):
        txt+=cmd%(fn, self.targetFolder)
      self.copyToClipboard(txt)
    else:
      if sel in (0, 1):     # copy / move files to target folder
        dlg=ExecutionProgressDialog(self, self.targetFolder, self.fileDict, sel)
        dlg.ShowModal()
        dlg.Destroy()
      elif sel==2:          # genisoimage
        volID=cfgfile.getLastVolumeID()
        imgNam=cfgfile.getLastImageName()
        dlg=VolIdImageNameDialog(self, imgNam, volID)
        if dlg.ShowModal()!=wx.ID_OK:
          dlg.Destroy()
          return
        imgNam, volID=dlg.getData()
        dlg.Destroy()
        cfgfile.setLastVolumeID(volID)
        cfgfile.setLastImageName(imgNam)

        # Inputfile für genisoimage mit den zu schreibenden Dateien unter /tmp anlegen
        tmpfile=os.path.join(tempfile.gettempdir(), "__fillBD2.tmp")
        with open(tmpfile, "w") as tmpObj:
          for fn, data in self.fileDict.items():
            if data.isFolder==True:
              tmpObj.write('%s=%s\n'%(data.filename.encode('utf8'), fn.encode('utf8')))
            elif data.isFile==True:
              tmpObj.write('%s\n'%fn.encode('utf8'))

        # das Kommando zum genisoimage-Aufruf ebenfalls unter /tmp ablegen, weil es einfacher
        # an den subprocess.Popen() übergeben werden kann.
        cmd='genisoimage -o "%s" %s -graft-points -V "%s" -path-list %s'%( \
             os.path.join(self.targetFolder, imgNam), self.getGenisoimageParm(), volID, tmpfile)
        cmdfile=os.path.join(tempfile.gettempdir(), "__fillBD2.sh")
        with open(cmdfile, "w") as cmdObj:
          cmdObj.write(cmd)
        dlg=ExecutionProgressDialog(self, self.targetFolder, self.fileDict, sel, ["sh", cmdfile])
        dlg.ShowModal()
        dlg.Destroy()
    self.EndModal(wx.ID_OK)

  # ###########################################################
  # Cancel-Button wurde gewählt.
  def cancelBut(self, event):
    self.EndModal(wx.ID_CANCEL)





# ###########################################################
# Der Dialog zum Kopieren von Dateien und Ordnern mit
# Fortschrittsanzeige.
# Bei Übergabe von "cmd" wird "cmd" ausgeführt und deren
# Meldungen werden angezeigt.
# Wird "cmd" nicht oder mit Leerstring übergeben, erfolgt
# die Ausführung einzelner cp- oder mv-Kommandos (gemäß
# "jobType") für die in "fileDict" gelisteten Dateien mit
# dem Ziel gemäß "targetFolder".
class ExecutionProgressDialog(wx.Dialog):
  def __init__(self, parent, targetFolder, fileDict, jobType, cmd=""):
    wx.Dialog.__init__(self, parent, wx.ID_ANY, "Progress", \
                        style=wx.CAPTION|wx.RESIZE_BORDER)
    self.parent=parent
    self.targetFolder=targetFolder
    self.fileDict=fileDict
    self.jobType=jobType    # 0=copy, 1=move
    self.cmd=cmd
    self.abortTransfer=False
    self.gauge_devisor=1  # mit "zu großen" Zahlen kann Gauge nicht umgehen

    if self.cmd=="":
      self.InitUI()
      self.Centre()
      wx.CallLater(50, self.executeCMDs)
    else:
      self.InitUIsimple()
      self.Centre()
      wx.CallLater(50, self.executeCMD)

  # ###########################################################
  # Fenster-Inhalt definieren
  def InitUIsimple(self):
    self.messages=wx.TextCtrl(self, wx.ID_ANY, "", size=(500, 200), \
                              style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL)
    self.ok=wx.Button(self, wx.ID_OK, "&Ok")
    self.cancel=wx.Button(self, wx.ID_CANCEL, "&Cancel")
    self.ok.Bind(wx.EVT_BUTTON, self.okBut)
    self.cancel.Bind(wx.EVT_BUTTON, self.cancelBut)

    vsizer=wx.BoxSizer(wx.VERTICAL)

    hsizer2=wx.BoxSizer(wx.HORIZONTAL)
    hsizer2.Add(self.ok,          0, wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT, 4)
    hsizer2.Add(self.cancel,      0, wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT, 4)

    vsizer.Add(self.messages,     1, wx.ALL|wx.EXPAND,                  4)
    vsizer.Add(hsizer2,           0, wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT, 4)

    self.SetSizer(vsizer)
    vsizer.Fit(self)
    self.ok.Disable()
    self.cancel.SetFocus()

  # ###########################################################
  # Fenster-Inhalt definieren
  def InitUI(self):
    self.sumBytesToCopy=sbtc=self.getSizeSum(self.fileDict)
    while sbtc>10000:
      sbtc/=10
      self.gauge_devisor*=10

    txt1=wx.StaticText(self, label="Number of objects:")
    self.objToCopy=wx.TextCtrl(self, wx.ID_ANY, "", size=(50, -1), style=wx.TE_READONLY)
    self.objToCopy.SetValue(hlp.intToStringWithCommas(len(self.fileDict)))
    txt2=wx.StaticText(self, label="Bytes in total:")
    self.bytesToCopy=wx.TextCtrl(self, wx.ID_ANY, "", size=(150, -1), style=wx.TE_READONLY)
    self.bytesToCopy.SetValue(hlp.intToStringWithCommas(self.sumBytesToCopy))
    txt3=wx.StaticText(self, label="Bytes current:")
    self.currentBytes=wx.TextCtrl(self, wx.ID_ANY, "", size=(150, -1), style=wx.TE_READONLY)
    txt4=wx.StaticText(self, label="Remaining objects:")
    self.objRemain=wx.TextCtrl(self, wx.ID_ANY, "", size=(50, -1), style=wx.TE_READONLY)
    txt5=wx.StaticText(self, label="Remaining bytes:")
    self.bytesRemain=wx.TextCtrl(self, wx.ID_ANY, "", size=(150, -1), style=wx.TE_READONLY)

    self.messages=wx.TextCtrl(self, wx.ID_ANY, "", size=(-1, 200), \
                              style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL)

    self.progBar=wx.Gauge(self, wx.ID_ANY, self.sumBytesToCopy//self.gauge_devisor, size=(1000, -1))

    self.ok=wx.Button(self, wx.ID_OK, "&Ok")
    self.cancel=wx.Button(self, wx.ID_CANCEL, "&Cancel")
    self.ok.Bind(wx.EVT_BUTTON, self.okBut)
    self.cancel.Bind(wx.EVT_BUTTON, self.cancelBut)

    vsizer=wx.BoxSizer(wx.VERTICAL)
    gsizer=wx.GridBagSizer(4, 4)
    sl=wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
    st=wx.RIGHT
    gsizer.Add(txt1,                (0, 0), (1, 1), sl|wx.TOP,        4)
    gsizer.Add(self.objToCopy,      (0, 1), (1, 1), st|wx.TOP,        4)
    gsizer.Add(txt2,                (0, 2), (1, 1), sl|wx.TOP,        4)
    gsizer.Add(self.bytesToCopy,    (0, 3), (1, 1), st|wx.TOP,        4)
    gsizer.Add(wx.StaticLine(self), (1, 0), (1, 6), wx.ALL|wx.EXPAND, 4)
    gsizer.Add(txt3,                (2, 0), (1, 1), sl|wx.BOTTOM,     4)
    gsizer.Add(self.currentBytes,   (2, 1), (1, 1), st|wx.BOTTOM,     4)
    gsizer.Add(txt4,                (2, 2), (1, 1), sl|wx.BOTTOM,     4)
    gsizer.Add(self.objRemain,      (2, 3), (1, 1), st|wx.BOTTOM,     4)
    gsizer.Add(txt5,                (2, 4), (1, 1), sl|wx.BOTTOM,     4)
    gsizer.Add(self.bytesRemain,    (2, 5), (1, 1), st|wx.BOTTOM,     4)

    # eigener Sizer für Gauge, damit das nur horizontal EXPANDed wird
    hsizer1=wx.BoxSizer(wx.HORIZONTAL)
    hsizer1.Add(self.progBar, 1)

    hsizer2=wx.BoxSizer(wx.HORIZONTAL)
    hsizer2.Add(self.ok,          0, wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT, 4)
    hsizer2.Add(self.cancel,      0, wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT, 4)

    vsizer.Add(gsizer,            0, wx.LEFT|wx.RIGHT|wx.EXPAND,        4)
    vsizer.Add(self.messages,     1, wx.ALL|wx.EXPAND,                  4)
    vsizer.Add(hsizer1,           0, wx.ALL|wx.EXPAND,                  4)
    vsizer.Add(hsizer2,           0, wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT, 4)

    self.SetSizer(vsizer)
    vsizer.Fit(self)
    self.ok.Disable()
    self.cancel.SetFocus()

  # ###########################################################
  # Führt ein einzelnes Kommando gemäß "self.cmd" aus und
  # stellt dessen Textausgabe dar.
  def executeCMD(self):
    self.executeSingleCMD(self.cmd)
    self.ok.Enable()        # Schließen des Dialoges freischalten
    self.cancel.Disable()   # der Cancel-Button wird jetzt nicht mehr gebraucht

  # ###########################################################
  # Führt gemäß "self.jobType" copy- oder move-Kommandos für
  # alle Ordner/Dateien in "self.fileDict" nach
  # "self.targetFolder" aus und stellt dabei den Fortschritt 
  # sowie den Erfolgsstatus dar.
  def executeCMDs(self):
    progBarVal=0
    cnt=len(self.fileDict)

    self.messages.SetValue("")

    if self.jobType==0:
      cmd=["cp", "-rp"]
    elif self.jobType==1:
      cmd=["mv"]
    else:
      self.EndModal(wx.ID_CANCEL)

    if DEBUG_FS==True:
      countup=bnls=0
      formatstrg="{0:15} {1:15} {2:15} {3:15} {4:15} {5:5} {6:15}"

    # nach filename sortiert über "self.fileDict" iterieren
    for k in OrderedDict(sorted(self.fileDict.items(), key=lambda t: t[1].filename)):
      v=self.fileDict[k]
      cmdToExecute=cmd+[k, self.targetFolder] # Kommando zusammensetzen

      self.messages.AppendText(   self.listToString(cmdToExecute)+"\n")
      self.currentBytes.SetValue( hlp.intToStringWithCommas(v.sizeAdj))
      self.objRemain.SetValue(    hlp.intToStringWithCommas(cnt))
      self.bytesRemain.SetValue(  hlp.intToStringWithCommas(self.sumBytesToCopy-progBarVal))
      wx.Yield()

      if DEBUG_FS==True:
        szv=os.statvfs(self.targetFolder)
        sv=szv.f_bavail*szv.f_bsize       # Dateisystem-Restgröße vor dem copy

      self.executeSingleCMD(cmdToExecute)

      if self.abortTransfer==True:                          # Abbruch-Wunsch weiterreichen
        break
      cnt-=1
      progBarVal+=v.sizeAdj   # Fortschritt abhängig von der aktuellen Dateigröße...
      self.progBar.SetValue(progBarVal//self.gauge_devisor)  # ...darstellen
      wx.Yield()

      if DEBUG_FS==True:
        countup+=1                        # Nummer der bearbeiteten Datei
        szn=os.statvfs(self.targetFolder)
        sn=szn.f_bavail*szn.f_bsize       # Dateisystem-Restgröße nach dem copy
        delta1=(sv-sn)                    # bei letztem copy belegte Byte
        delta2=delta1-v.sizeAdj           # Differenz der belegten Byte zur Dateigröße (also der Fehler)
        bn=os.path.basename(k)            # Dateiname der gerade kopierten Datei
        bnls+=len(bn)                     # Länge der bisher kopierten Dateinamen
        print formatstrg.format(sv, sn, delta1, v.sizeAdj, delta2, countup, bn)

    self.currentBytes.SetValue( "0")
    self.objRemain.SetValue(    "0")
    self.bytesRemain.SetValue(  "0")

    self.ok.Enable()        # Schließen des Dialoges freischalten
    self.cancel.Disable()   # der Cancel-Button wird jetzt nicht mehr gebraucht

  # ###########################################################
  # Führt die Befehle in der Liste "cmdToExecute" aus und
  # zeigt eventuell gelieferte Texte im TextCtrl an. Wechselt
  # "self.abortTransfer" auf "True", wird der Prozess gekillt
  # und somit abgebrochen.
  def executeSingleCMD(self, cmdToExecute):
    process=subprocess.Popen(cmdToExecute, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:   # Loop, weil der subprocess ggf. mehrere Zeilen liefert, Ausstieg via break
      while not select.select([process.stdout], [], [], 0)[0]:  # solange nix auf der stdout-pipe...
        if self.abortTransfer==True:                      # auf Abbruch-Wunsch testen
          process.kill()                                  # auf Wunsch den Popen-Prozess killen
          self.messages.AppendText("<< killed >>\n")      # und das anzeigen
          break
        wx.Yield()
        time.sleep(0.01)
      if self.abortTransfer==True:                        # Abbruch-Wunsch weiterreichen
        break

      line=process.stdout.readline()                      # Rückgabe von Popen-Prozess holen
      if line=="":                                        # wenn Fertigmeldung...
        break                                             # ...Schleife verlassen
      try:
        self.messages.AppendText(line.strip()+"\n")       # sonst [Fehler]-Meldung anzeigen
      except Exception, e:
        self.messages.AppendText("ERROR: "+str(e)+"\n")
        if wx.MessageBox(str(e), "Error", wx.OK|wx.CANCEL|wx.ICON_ERROR)==wx.CANCEL:
          break

  # ###########################################################
  # Liefert die Gesamtgröße der Dateien und Ordner in
  # "fileDict".
  def getSizeSum(self, fileDict):
    ssum=0
    for k, v in fileDict.items():
      ssum+=v.sizeAdj
    return(ssum)

  # ###########################################################
  # Liefert zu einer Liste eine etwas hübschere Repäsentation,
  # als str(lst) es täte.
  def listToString(self, lst):
    s=""
    for l in lst:
      s+=' '+l
    return(s[1:])

  # ###########################################################
  # Ok-Button wurde gewählt.
  def okBut(self, event):
    self.EndModal(wx.ID_OK)   # Dialog beenden

  # ###########################################################
  # Cancel-Button wurde gewählt.
  def cancelBut(self, event):
    self.abortTransfer=True   # Abbruch-Wunsch vermerken
    self.ok.Enable()          # Schließen des Dialoges freischalten
    self.cancel.Disable()     # der Cancel-Button wird jetzt nicht mehr gebraucht





# ###########################################################
# Ein Dialog zur Abfrage von Image-Name und Volume-ID für
# genisoimage.
class VolIdImageNameDialog(wx.Dialog):
  def __init__(self, parent, imgnam, volid):
    wx.Dialog.__init__(self, parent, wx.ID_ANY, "Filename / Label", \
                        style=wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER)
    self.parent=parent
    self.imgnam=imgnam
    self.volid=volid

    self.InitUI()
    self.Centre()

  # ###########################################################
  # Fenster-Inhalt definieren
  def InitUI(self):
    txt1=wx.StaticText(self, label="Filename/Image:")
    self.imgName=wx.TextCtrl(self, wx.ID_ANY, self.imgnam, size=(150, -1))
    txt2=wx.StaticText(self, label="Volume ID:")
    self.volumeID=wx.TextCtrl(self, wx.ID_ANY, self.volid, size=(150, -1))

    self.imgName.Bind(wx.EVT_TEXT, self.imgNameChanged)
    self.volumeID.Bind(wx.EVT_TEXT, self.volumeIDChanged)

    self.ok=wx.Button(self, wx.ID_OK, "&Ok")
    self.cancel=wx.Button(self, wx.ID_CANCEL, "&Cancel")
    self.ok.Bind(wx.EVT_BUTTON, self.okBut)
    self.cancel.Bind(wx.EVT_BUTTON, self.cancelBut)

    vsizer=wx.BoxSizer(wx.VERTICAL)
    gsizer=wx.GridBagSizer(4, 4)
    sl=wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
    st=wx.RIGHT
    gsizer.Add(txt1,          (0, 0), (1, 1), sl|wx.TOP,              4)
    gsizer.Add(self.imgName,  (0, 1), (1, 1), st|wx.TOP|wx.EXPAND,    4)
    gsizer.Add(txt2,          (1, 0), (1, 1), sl|wx.BOTTOM,           4)
    gsizer.Add(self.volumeID, (1, 1), (1, 1), st|wx.BOTTOM|wx.EXPAND, 4)
    gsizer.AddGrowableCol(1, 1)

    hsizer=wx.BoxSizer(wx.HORIZONTAL)
    hsizer.Add(self.ok,     0, wx.ALL|wx.ALIGN_RIGHT, 4)
    hsizer.Add(self.cancel, 0, wx.ALL|wx.ALIGN_RIGHT, 4)

    vsizer.Add(gsizer,      0, wx.ALL|wx.EXPAND,      4)
    vsizer.Add(hsizer,      0, wx.ALL|wx.ALIGN_RIGHT, 4)

    self.SetSizer(vsizer)
    vsizer.Fit(self)
    self.imgName.SetFocus()
    self.checkForEnableOkButton()

  # ###########################################################
  # "self.imgName" wurde geändert.
  def imgNameChanged(self, event):
    self.checkForEnableOkButton()

  # ###########################################################
  # "self.volumeID" wurde geändert.
  def volumeIDChanged(self, event):
    self.checkForEnableOkButton()

  # ###########################################################
  # Setzt je nach Inhalt der TextCtrls einen ToolTip und
  # aktiviert nur dann den ok-Button, wenn beide Felder
  # valide Daten enthalten.
  def checkForEnableOkButton(self):
    enable_ok1=enable_ok2=False
    imgnam=self.imgName.GetValue()
    chk=self.checkStrg(imgnam)
    if chk==1:
      self.imgName.SetBackgroundColour("MAGENTA")
      self.imgName.SetToolTip(wx.ToolTip("Text too long! (max. 32 characters)"))
    elif chk==2:
      self.imgName.SetBackgroundColour("MAGENTA")
      self.imgName.SetToolTip(wx.ToolTip("non-ASCII-characters detected"))
    else:
      self.imgName.SetBackgroundColour(wx.NullColor)
      self.imgName.SetToolTip(wx.ToolTip.Enable(False))
      enable_ok1=True

    volid=self.volumeID.GetValue()
    chk=self.checkStrg(volid)
    if chk==1:
      self.volumeID.SetBackgroundColour("MAGENTA")
      self.volumeID.SetToolTip(wx.ToolTip("Text too long! (max. 32 characters)"))
    elif chk==2:
      self.volumeID.SetBackgroundColour("MAGENTA")
      self.volumeID.SetToolTip(wx.ToolTip("non-ASCII-characters detected"))
    else:
      self.volumeID.SetBackgroundColour(wx.NullColor)
      self.volumeID.SetToolTip(wx.ToolTip.Enable(False))
      enable_ok2=True

    if enable_ok1==True and enable_ok2==True:
      self.ok.Enable()
    else:
      self.ok.Disable()

  # ###########################################################
  # Liefert 1, wenn strg mehr als 32 Zeichen enthält,
  # liefert 2, wenn strg non-ASCII-Zeichen enthält und
  # liefert ansonsten 0.
  def checkStrg(self, strg):
    if len(strg)>32:
      return(1)
    try:
      dummy=str(strg)
    except:
      return(2)
    return(0)

  # ###########################################################
  # Ok-Button wurde gewählt.
  def okBut(self, event):
    self.EndModal(wx.ID_OK)

  # ###########################################################
  # Cancel-Button wurde gewählt.
  def cancelBut(self, event):
    self.EndModal(wx.ID_CANCEL)

  # ###########################################################
  # Liefert den Inhalt der beiden TextCtrls als Tupel aus zwei
  # Strings (imgnam, volid).
  def getData(self):
    return((self.imgName.GetValue(), self.volumeID.GetValue()))

