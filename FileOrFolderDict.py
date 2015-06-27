#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


# ###########################################################
# Ein Satz eines FileOrFolderDict-Objektes.
class FileOrFolder():
  def __init__(self):
    self.index=0            # ein Index
    self.fullname=""        # der komplette Name mit Pfad der Datei oder des Ordners
    self.foldername=""      # der Ordner-Name
    self.filename=""        # der Datei-Name
    self.size=0             # die Datei-Größe (bei Ordnern die Größe aller enthaltenen Dateien und Ordner)
    self.sizeAdj=0          # wie self.size, allerdings auf Blockgröße ausgerichtet
    self.usedBlocksize=0    # die zur Berechnung von self.sizeAdj verwendete Blockgröße
    self.isFolder=False     # Flag, obs ein Ordner ist
    self.isFile=False       # Flag, obs eine Datei ist
    self.isSymLink=False    # Flag, obs eine symbolische Verknüpfung ist
    self.hasErrors=False    # Flag, ob Ordner illegale Unter-Objekte enthält (bzgl. Encoding)

# ###########################################################
# Eine Klasse zur Verwaltung eines Dictionaries mit
# key  =voller Pfad + Datei-/Ordner-Name
# value=ein FileOrFolder-Objekt
class FileOrFolderDict():
  def __init__(self):
    self.clear()

  # ###########################################################
  # Löscht alle Sätze des Dictionarys.
  def clear(self):
    self.obj={}     # hier liegen die Daten, Index ist der komplette Dateiname
    self.objidx={}  # ein Index für "index" auf den Key von "self.obj"
    self.nextIndex=0

  # ###########################################################
  # Liefert True, wenn "fileOrFolder" vorhanden und lesbar ist.
  def isValid(self, fileOrFolder):
    try:
      # wenn die Größe nicht ermittelt werden kann...
      sz=os.path.getsize(fileOrFolder)
    except:
      # ...dann wird das DateisystemObjekt ignoriert
      return(False)

    if os.access(fileOrFolder, os.F_OK|os.R_OK)==False:
      # wenn kein Leserecht, ebenfalls ignorieren
      return(False)

    return(True)

  # ###########################################################
  # Fügt den Datei- oder Ordner-Namen in "fileOrFolder" dem
  # Dictionary hinzu.
  #
  # Returncodes:
  #  0 : "fileOrFolder" wurde dem Dictionary zugefügt
  #  1 : im Dictionary vorhandene Unterordner von "fileOrFolder"
  #      wurden gelöscht und stattdessen "fileOrFolder" aufgenommen
  #  2 : auf "fileOrFolder" konnte nicht zugegriffen werden
  #  3 : "fileOrFolder" war schon im Dictionary enthalten
  #  4 : ein übergeordneter Ordner von "fileOrFolder" befindet sich
  #      bereits im Dictionary. Daher wurde "fileOrFolder" nicht
  #      aufgenommen
  #  5 : ein gleichnamiges Objekt auf unterster Ebene befindet sich
  #      bereits im Dictionary
  def insertFileOrFolder(self, fileOrFolder, size, sizeAdj, hasErrors=False):
    if fileOrFolder in self.obj:
      # Objekt ist schon identisch im Dictionary enthalten
      return(3)

    data=FileOrFolder()
    data.fullname=fileOrFolder
    data.hasErrors=hasErrors

    if os.path.islink(fileOrFolder)==True:
      data.isSymLink=True
    if os.path.isfile(fileOrFolder)==True:
      data.isFile=True
      data.foldername=os.path.dirname(fileOrFolder)
      data.filename=os.path.basename(fileOrFolder)
    elif os.path.isdir(fileOrFolder)==True:
      data.isFolder=True
      data.foldername=os.path.dirname(fileOrFolder)
      data.filename=os.path.basename(fileOrFolder)
    else:
      #print "Error: not file nor folder", fileOrFolder
      return(2)

    rc=0
    if data.isFolder==True: new=data.fullname+"/"
    else:                   new=data.foldername+"/"

    for k, v in self.obj.items():
      if v.isFolder==True:  old=v.fullname+"/"
      else:                 old=v.foldername+"/"

      cp=os.path.commonprefix([new, old])
      if data.isFolder==True and cp==new:
        # wenn ein Ordner eingefügt werden soll, von dem
        # bereits Unterordner im Dictionary enthalten sind,
        # dann sind diese Unterordner zu löschen.
        del self.obj[k]
        rc=1
      if v.isFolder==True and cp==old:
        # ein übergeordneter Ordner befindet sich schon im Dictionary
        return(4)
      if data.filename==v.filename:
        return(5)

    data.size=size
    data.sizeAdj=sizeAdj

    data.index=self.nextIndex
    self.nextIndex+=1
    self.obj.update({fileOrFolder : data})
    self.objidx.update({data.index : fileOrFolder})
    return(rc)

  # ###########################################################
  # Löscht einen Satz aus dem Dictionary anhalt seines Keys
  # bzw. fullnames.
  def remove(self, fileOrFolder):
    obj=self.obj.get(fileOrFolder, None)
    if obj!=None:
      del self.objidx[obj.index]
      del self.obj[fileOrFolder]

  # ###########################################################
  # Löscht einen Satz aus dem Dictionary anhalt seines Wertes
  # in "index".
  def removeByIndex(self, index):
    idx=self.objidx.get(index, None)
    if idx!=None:
      del self.obj[idx]
      del self.objidx[index]
      return(True)
    return(False)

  # ###########################################################
  # Liefert zu einem index das entspr. FileOrFolder-Objekt.
  # Oder None, wenn zu index ein solches nicht existiert.
  def getFileOrFolder(self, index):
    idx=self.objidx.get(index, None)
    if idx!=None:
      return(self.obj.get(idx, None))
    return(None)

  # ###########################################################
  # Liefert die Daten für einen fullname.
  def getByFullname(self, fullname):
    return(self.obj.get(fullname, None))

  # ###########################################################
  # Anzeige der Daten aller Objekte
  def debugPrint(self):
    for k, v in self.obj.items():
      print v.index, v.foldername, v.filename, v.size, v.sizeAdj, \
            v.usedBlocksize, v.isFolder, v.isFile, v.isSymLink
#    for k, v in self.objidx.items():
#      print k, v

