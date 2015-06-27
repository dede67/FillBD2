#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import wx

CFGFILE=os.path.join(os.path.expanduser('~'), ".fillBD.conf")

# ###########################################################
# Fenster-Größe und -Position lesen/schreiben.
def getWindowSize():
  fc=wx.FileConfig(localFilename=CFGFILE)
  posx=fc.ReadInt("pos_x", -1)
  posy=fc.ReadInt("pos_y", -1)
  sizex=fc.ReadInt("size_x", 1200)
  sizey=fc.ReadInt("size_y", 700)
  pos=(posx, posy)    # (-1, -1) entspricht wx.DefaultPosition
  size=(sizex, sizey) # (-1, -1) entspricht wx.DefaultSize
  del fc
  return((pos, size))
# -----------------------------------------------------------
def setWindowSize(pos, size):
  fc=wx.FileConfig(localFilename=CFGFILE)
  fc.WriteInt("pos_x",    pos[0])
  fc.WriteInt("pos_y",    pos[1])
  fc.WriteInt("size_x" ,  size[0])
  fc.WriteInt("size_y" ,  size[1])
  fc.Flush()
  del fc




# ###########################################################
# Zuletzt ausgewähltes Target-Profil lesen/schreiben.
def getLastSelectedDestProfile():
  fc=wx.FileConfig(localFilename=CFGFILE)
  profileName=fc.Read("last_dest_profile", "")
  del fc
  return(profileName)
# -----------------------------------------------------------
def setLastSelectedDestProfile(profileName):
  fc=wx.FileConfig(localFilename=CFGFILE)
  fc.Write("last_dest_profile", profileName)
  fc.Flush()
  del fc




# ###########################################################
# Maximal-Rechenzeit lesen/schreiben.
def getCalcTime():
  fc=wx.FileConfig(localFilename=CFGFILE)
  calcTime=fc.ReadInt("calc_time", 10)
  del fc
  return(calcTime)
# -----------------------------------------------------------
def setCalcTime(calcTime):
  fc=wx.FileConfig(localFilename=CFGFILE)
  fc.WriteInt("calc_time", calcTime)
  fc.Flush()
  del fc




# ###########################################################
# Spalten-Breiten der beiden ListCtrls lesen/schreiben.
COL_NAM=[ ["colW1_path", "colW1_name", "colW1_size", "colW1_sizeAdj"],
          ["colW2_name", "colW2_sizeAdj"] ]
COL_DEF=[ [240, 320, 92, 92],
          [308, 92]  ]
# -----------------------------------------------------------
def getColWidth(ctrl_nr):
  if ctrl_nr not in (1, 2):
    return([])
  fc=wx.FileConfig(localFilename=CFGFILE)
  lst=[]
  for v in range(len(COL_NAM[ctrl_nr-1])):
    lst.append(fc.ReadInt(COL_NAM[ctrl_nr-1][v], COL_DEF[ctrl_nr-1][v]))
  del fc
  return(lst)
# -----------------------------------------------------------
def setColWidth(ctrl_nr, colList):
  if ctrl_nr not in (1, 2):
    return
  fc=wx.FileConfig(localFilename=CFGFILE)    
  for c in range(len(colList)):
    fc.WriteInt(COL_NAM[ctrl_nr-1][c], colList[c])
  fc.Flush()
  del fc




# ###########################################################
# Spalten-Sortierung der ListCtrls lesen/schreiben.
def getColSort(ctrl_nr):
  if ctrl_nr not in (1, 2):
    return(())
  fc=wx.FileConfig(localFilename=CFGFILE)
  c=fc.ReadInt("SortColNum_"+str(ctrl_nr-1), 0)
  d=fc.ReadInt("SortColDir_"+str(ctrl_nr-1), 0)
  del fc
  return((c, d))
# -----------------------------------------------------------
def setColSort(ctrl_nr, sortOrder):
  if ctrl_nr not in (1, 2):
    return
  fc=wx.FileConfig(localFilename=CFGFILE)    
  fc.WriteInt("SortColNum_"+str(ctrl_nr-1), sortOrder[0])
  fc.WriteInt("SortColDir_"+str(ctrl_nr-1), sortOrder[1])
  fc.Flush()
  del fc




# ###########################################################
# Zuletzt genutzte VolumeID für genisoimage lesen/schreiben.
def getLastVolumeID():
  fc=wx.FileConfig(localFilename=CFGFILE)
  volID=fc.Read("LastVolumeID", "my DVD label")
  del fc
  return(volID)
# -----------------------------------------------------------
def setLastVolumeID(volID):
  fc=wx.FileConfig(localFilename=CFGFILE)    
  fc.Write("LastVolumeID", volID)
  fc.Flush()
  del fc




# ###########################################################
# Zuletzt genutzter Image-Name für genisoimage lesen/schreiben.
def getLastImageName():
  fc=wx.FileConfig(localFilename=CFGFILE)
  imgnam=fc.Read("LastImageName", "image.iso")
  del fc
  return(imgnam)
# -----------------------------------------------------------
def setLastImageName(imgnam):
  fc=wx.FileConfig(localFilename=CFGFILE)    
  fc.Write("LastImageName", imgnam)
  fc.Flush()
  del fc

