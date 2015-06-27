#!/usr/bin/env python
# -*- coding: utf-8 -*-




# ###########################################################
# Liefert die Zahl x mit Tausender-Trenn-Punkten.
def intToStringWithCommas(x):
  if type(x) is not int and type(x) is not long:
    #raise TypeError("Not an integer!")
    return(x)
  if x<0:
    return('-'+intToStringWithCommas(-x))
  elif x<1000:
    return(str(x))
  else:
    return(intToStringWithCommas(x/1000)+'.'+'%03d'%(x%1000))

# ###########################################################
# Liefert zu einer Zahl mit Tausender-Trenn-Punkten den
# numerischen Wert - konnte nicht nach int gewandelt werden,
# wird 0 geliefert.
def stringWithCommasToInt(strg):
  s=strg.replace(".", "")
  try:
    i=int(s)
  except:
    return(0)
  return(i)

# ###########################################################
# Liefert "num" in der passendsten Größenangabe.
def prettySize(num):
  for x in ['','KB','MB','GB', 'TB']:
    if num<1024.0:
      return("{0:4.0f} {1:s}".format(num, x))
    num/=1024.0

# ###########################################################
# Liefert den größten Wert von Key im Dictionary "d".
def getMaxIntegerKeyFromDict(d):
  mk=0
  for k in d.keys():
    mk=max(k, mk)
  return(mk)

# ###########################################################
# Liefert eine Darstellung von "strg", die im GUI dargestellt
# werden kann.
CODECS=["utf-8", "latin-1", "cp1252"]
def forceUTF8(strg):
  if type(strg)==unicode:
    return(strg)

  for c in CODECS:
    try:
      retstrg=strg.decode(c)
    except:
      continue
    return(retstrg)

  # wenns auf die nette Weise nicht geht, dann eben brutal
  retstrg=""
  for c in strg:
    if ord(c)>127:  # Und bist du nicht willig...
      c="?"         # ...so brauch' ich Gewalt
    retstrg+=c
  return(retstrg)

