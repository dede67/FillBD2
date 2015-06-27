#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs
import locale
import sys

class ConnectedFiles():
  def __init__(self, fileList):
    self.fileList=sorted(fileList)
    self.fileListLen=len(self.fileList)
    self.sequenceList=[]
    self.__processList()

  # ###########################################################
  # Liefert eine Liste der Dateinamen, die als mehrteilig
  # identifiziert wurden.
  def getConnectedFiles(self):
    return(self.sequenceList)

  # ###########################################################
  # Iteriert über alle Dateien, erkennt mehrteilige Dateien
  # und legt diese in der Liste "self.sequenceList" ab.
  def __processList(self):
    idx=0
    while idx<self.fileListLen:
      seqLen=self.__findCommonPrefixSequence(idx)
      if seqLen>1:
        self.sequenceList.append(self.fileList[idx])
        
#        print self.fileList[idx], seqLen, "-"*40
        for i in range(seqLen-1):
#          print self.fileList[idx+1+i]
          self.sequenceList.append(self.fileList[idx+1+i])
        idx+=seqLen
      else:
#        print "-"*40, self.fileList[idx]
        idx+=1

  # ###########################################################
  # Sucht ab dem Index "idx" in "self.fileList" nach
  # mehrteiligen Dateinamen und liefert die Anzahl
  # zusammengehöriger Dateinamen (ab idx).
  def __findCommonPrefixSequence(self, idx):
    if (idx+1)>=self.fileListLen: # wenn nicht mehr genug Elemente in der Liste sind...
      return(1)                   # ...Feierabend

    cp1=os.path.commonprefix([self.fileList[idx], self.fileList[idx+1]])  # Prefix bestimmen
    if len(cp1)<3:  # wenn Prefix zu kurz ist...
      return(1)     # ...als "keine Sequenz gefunden" zurückmelden
    if self.__checkSequence(idx, cp1, 2)==False:
      return(1)

    idx2=idx+2
    while (idx2)<self.fileListLen:  # solange noch Elemente in der Liste sind
      cp2=os.path.commonprefix([self.fileList[idx2-1], self.fileList[idx2]])  # nächsten Prefix bestimmen
      if cp1==cp2:    # wenn gleich zum ersten Prefix...
        if self.__checkSequence(idx, cp1, idx2-idx+1)==False:
          break
        idx2+=1       # ...weiter-testen
      else:
        break         # ...sonst Ende
    return(idx2-idx)

  # ###########################################################
  # Prüft für Dateinamen ab dem Index "idx" in "self.fileList",
  # ob nach len(prefix) Zeichen eine lückenlos aufsteigende
  # und freistehende Sequenz-Folgen-Kennung vorkommt.
  # Eine Sequenz-Folgen-Kennung muß entweder mit 0, 1 oder A
  # beginnen und dann entsprechend aufsteigen.
  def __checkSequence(self, idx, prefix, seqLen):
    if seqLen<2:
      return(False)
    prefixLen=len(prefix)
    sfkl=0   # Länge der Sequenz-Folgen-Kennung

    tmpPrefixLen=prefixLen
    if self.fileList[idx][prefixLen].isdigit(): # wenn erstes Zeichen nach Prefix eine Ziffer ist...
      # solange rückwärts gehen, bis Zeichen nicht mehr isdigit() ist
      while self.fileList[idx][tmpPrefixLen].isdigit():
        if tmpPrefixLen>0:
          tmpPrefixLen-=1
        else:
          break
      tmpPrefixLen+=1
      tmp2PrefixLen=tmpPrefixLen
      # solange vorwärts gehen, bis Zeichen nicht mehr isdigit() ist
      while self.fileList[idx][tmp2PrefixLen].isdigit():
        sfkl+=1
        tmp2PrefixLen+=1
        # Ende wird nicht geprüft, weil jeder String mit sowas wie ".ext" enden sollte
    elif self.fileList[idx][prefixLen].isalpha(): # wenn erstes Zeichen nach Prefix ein Buchstabe ist...
      sfkl=1  # es ist nur genau ein Zeichen erlaubt, wenn Sequenz-Folgen-Kennung ein Buchstabe ist
      # aber davor und dahinter darf kein Buchstabe stehen
      if self.fileList[idx][prefixLen-1].isalpha() or self.fileList[idx][prefixLen+1].isalpha():
        return(False)
    else:
      return(False)   # Sonderzeichen sind an dieser Stelle nicht erlaubt

    lst=[]
    for i in range(seqLen):   # über alle Dateinamen in der vermeintlichen Sequenz
      lst.append(self.fileList[idx+i][tmpPrefixLen:tmpPrefixLen+sfkl])  # vermeintliche Sequenz-Folgen-Kennung speichern

    #test1: sind alle Elemente Typ-gleich?
    if lst[0].isdigit():
      for i in lst:
        if not i.isdigit():
          return(False)
    elif lst[0].isalpha():
      for i in lst:
        if not i.isalpha():
          return(False)

    #test2: startet die Sequenz bei 0, 1, oder A und ist dann lückenlos aufsteigend?
    if lst[0].isdigit():    # für Ziffern
      e1=int(lst[0])
      if e1 not in (0, 1):  # wenn Sequenz nicht bei 0 oder 1 startet
        return(False)       # ist es keine legale Sequenz
      for i in range(1, len(lst)):  # auf lückenlos forlaufend prüfen
        if int(lst[i])==(e1+1):
          e1+=1
        else:
          return(False)
    elif lst[0].isalpha():  # für Buchstaben
      e1=ord(lst[0].upper())
      if e1!=ord("A"):      # wenn Sequenz nicht bei A oder a staret
        return(False)       # ist es keine legale Sequenz
      for i in range(1, len(lst)):  # auf lückenlos forlaufend prüfen
        if ord(lst[i].upper())==(e1+1):
          e1+=1
        else:
          return(False)
    return(True)  # alle Tests erfolgreich durchlaufen -> ist eine legale Sequenz der Länge "seqLen"


# ###########################################################
# 
if __name__=='__main__':
  sys.stdout=codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

  filenames=os.listdir("/4TB/filme_temp3/auf_usb_platte_und_bd_aber_ungesehen")
  for i in xrange(len(filenames)):
    filenames[i]=filenames[i].decode('utf-8')
  cf=ConnectedFiles(filenames)

  print "*"*80

  cfl=cf.getConnectedFiles()
  for fn in cfl:
    print fn



