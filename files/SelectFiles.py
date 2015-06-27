#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx

import time

import Helpers as hlp


# ###########################################################
# Klasse zur Zusammenstellung der Dateien in "fileList", so
# daß die Summe der Dateigrößen möglichst nah an "destSize"
# liegt. Abbruchkriterium ist eine Restgröße kleiner/gleich
# "blockSize" oder eine Rechenzeit über "timeout" Sekunden.
# Es erfolgt eine Ausgabe bei jeder besseren gefundenen
# Zusammenstellung.
class SelectFiles(wx.Dialog):
  def __init__(self, parent, fileList, destSize, blockSize, timeout):
    wx.Dialog.__init__(self, parent, wx.ID_ANY, "Status", style=wx.CAPTION|wx.RESIZE_BORDER)

    self.parent=parent
    self.fileList=fileList
    self.destSize=destSize
    self.blockSize=blockSize
    self.timeout=timeout
    self.cnt=0

    self.fileList.insert(0, ("/dev/null", 0))
    self.fileListCount=len(self.fileList)

    self.InitUI()
    self.Centre()
    self.Show()
    wx.Yield()

    self.sumList=self.__buildSums()
    self.startTime=time.clock()
    self.statusWordCount=0
    self.bitmap, dontCare, dontCare, error=self.__findArrangement(0, 0, self.destSize, 0)
    if error==1:
      self.insertLine("Timeout!")
    elif error==2:
      self.insertLine("Too many files for the root directory!\nError: maximum recursion depth exceeded")
    self.enableOkButton()

  # ###########################################################
  # Fenster-Inhalt definieren
  def InitUI(self):
    vsizer=wx.BoxSizer(wx.VERTICAL)

    self.msg=wx.ListBox(self, wx.ID_ANY, size=(-1, 400))
    sz=self.msg.GetFont().GetPointSize()  # Default-Font-Size
    self.msg.SetFont(wx.Font(sz, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    # eine Zeile mit Leerzeichen einfügen, damit der Sizer die
    # benötigte Breite korrekt einstellen kann
    self.msg.AppendAndEnsureVisible(" "*min(self.fileListCount+10, 150))
    #print "self.fileListCount=", self.fileListCount

    vsizer.Add(self.msg, 1, wx.ALL|wx.EXPAND, 1)

    self.ok=wx.Button(self, label="Ok")
    self.ok.Disable()
    self.ok.Bind(wx.EVT_BUTTON, self.okBut)
    self.ok.SetDefault()
    vsizer.Add(self.ok, 0, wx.ALIGN_RIGHT, 1)

    self.msg.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
    self.ok.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)

    self.SetSizer(vsizer)
    vsizer.Fit(self)
    self.msg.SetFocus()

  # ###########################################################
  # Fügt eine Zeile "line" ein und scrollt ggf. das Fenster, um
  # die neue Zeile in den sichtbaren Bereich zu bringen.
  def insertLine(self, line):
    self.msg.AppendAndEnsureVisible(line)

  # ###########################################################
  # Schaltet den Ok-Button frei.
  def enableOkButton(self):
    self.ok.Enable()

  # ###########################################################
  # Ok-Button wurde gewählt.
  def okBut(self, event):
    self.Close()

  # ###########################################################
  # Schließt das Fenster bei ESC.
  def onKeyDown(self, event):
    key=event.GetKeyCode()
    if key==wx.WXK_ESCAPE:
      self.Close()
    event.Skip()

  # ###########################################################
  # Liefert "val" als Dualzahl in der Länge "lng-1".
  # Das unterste Bit wird abgeschnitten.
  # "0" wird durch "-" und "1" durch "X" ersetzt.
  def __int2dual(self, val, lng):
    d="-"*lng + bin(val)[2:].replace("0", "-").replace("1", "X")
    e=d[len(d)-lng:]
    return(e[:len(e)-1])

  # ###########################################################
  # Liefert eine Liste mit den Summen der Dateigrößen, die ab
  # dem jeweiligen Index in "self.fileList" noch kommen.
  # Dadurch kann im rekursiven Abstieg erkannt werden, ob
  # überhaupt noch genug Dateien verfügbar sind, um eine bessere
  # Restkapazität zu erreichen.
  def __buildSums(self):
    lst=[]
    cursum=0
    for i in range(self.fileListCount-1, -1, -1): # von klein nach groß
      cursum+=self.fileList[i][1]                 # Zwischensummen bilden
      lst.append(cursum)                          # und ablegen
    lst.reverse() # Liste umdrehen, damit auf Index 0 die Gesamtsumme landet
    return(lst)

  # ###########################################################
  # Liefert eine Bitmap für die Datei-Zusammenstellung.
  # Rückgabe ist ein Tupel aus:
  #   (bitmap, restkapazität, Lösung gefunden[Bool], Fehler[0,1,2])
  #    Fehler: 0=kein Fehler, 1=Timeout, 2=zu viele Files
  def __findArrangement(self, index, currentSize, bestRemainSize, bitmap, error=0):
    newSize=currentSize+self.fileList[index][1]     # aktuelle Dateigröße zufügen
    bitmap|=(2**index)                              # und in der Bitmap vermerken
    done=False
    self.cnt+=1

    if newSize<self.destSize:           # wenn es noch gepasst hat
      remainSize=self.destSize-newSize  # neue Restkapazität berechnen

      # wenn dabei neue beste Zusammenstellung gefunden wurde
      if remainSize>0 and remainSize<bestRemainSize:
        bestRemainSize=remainSize # ...merken

        if self.fileListCount>100:  # bei zu vielen Dateien dauert die Anzeige zu lange
          s1=self.__int2dual(bitmap, self.fileListCount)
          s2=s1.replace("-", " ")
          s3=s2.split()
          ls3=len(s3)
          if ls3>1: # erst dann mit der Ausgabe beginnen, wenn mindestens eine Datei ausgelassen wurde
            if ls3!=self.statusWordCount:  # und sich zur vorigen Ausgabe deutlich was geändert hat
              self.statusWordCount=ls3
              self.insertLine(s1+" "+hlp.prettySize(bestRemainSize))
        else:
          self.insertLine(self.__int2dual(bitmap, self.fileListCount)+" "+hlp.prettySize(bestRemainSize))

        # bei maximal "self.blockSize" Restkapazität...
        if bestRemainSize<=self.blockSize:
          # ist das gut genug -> Rekursion beenden
          return(bitmap, bestRemainSize, True, error)

      wx.Yield()

      # Optimierung1: wenn Restkapazität kleiner als die kleinste Datei...
      if remainSize<self.fileList[self.fileListCount-1][1]:
        # dann macht es hier keinen Sinn mehr, weiter zu testen
        return(bitmap, bestRemainSize, done, error)

      if (time.clock()-self.startTime)>self.timeout:  # Abbruch nach n Sekunden
        return(bitmap, bestRemainSize, True, 1)

      # wenn nicht bereits die letzte Datei erreicht wurde
      if index<self.fileListCount:
        bitmap2=bitmap    # Bitmap sichern

        # rekursiver Abstieg für alle möglichen kleineren Dateigrößen
        for i in range(1, self.fileListCount-index):
          # Optimierung2: wenn die Summe der Dateigrößen der noch zu testenden Dateien
          # nicht mehr reicht, um eine bessere "bestRemainSize" zu erreichen...
          if (self.destSize-(newSize+self.sumList[index+i]))>bestRemainSize:
            # ...brauchts auch nicht getestet werden
            break

          try:
            bm, br, done, error=self.__findArrangement(index+i, newSize, bestRemainSize, bitmap, error)
          except: # ggf. maximum recursion depth exceeded
            return(bitmap, bestRemainSize, True, 2)

          # wenn neue beste Zusammenstellung gefunden
          if br<bestRemainSize:
            bestRemainSize=br # Restkapazität merken
            bitmap2=bm        # und Bitmap nach der Schleife an Aufrufer übergeben

          # wenn Zusammenstellung mit maximal "self.blockSize" Restkapazität gefunden wurde
          if done==True:
            break # Schleife abbrechen und Rekursion beenden

        # möglicherweise gefundene bessere Bitmap einstellen oder sonst alte Bitmap wiederherstellen
        bitmap=bitmap2
    return(bitmap, bestRemainSize, done, error)

  # ###########################################################
  # Liefert eine Liste von Tupeln mit den ausgewählten Dateien
  # und deren Gesamtgröße. Die Tupel haben den Aufbau
  #   (Dateiname, GrößeAdj, Größe)
  def getFiles(self):
    lst=[]
    curSum=0
    for j in range(1, self.fileListCount):  # startet bei 1, um die leere Datei zu überspringen
      if self.bitmap&(2**j)>0:
        lst.append((self.fileList[j][0], self.fileList[j][1], self.fileList[j][2]))
        curSum+=self.fileList[j][1]
    return(lst, curSum)

  # ###########################################################
  # Liefert die Anzahl der getesteten Zusammenstellungen.
  def getTestsCounter(self):
    return(self.cnt)


