#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os

HOMEDIR=os.path.expanduser('~')
DATABASENAME=os.path.join(HOMEDIR, ".fillBD.conf.sqlite")

# ###########################################################
# DB-Zugriff für die Profile
class Database():
  def __init__(self):
    self.dbname=DATABASENAME

    if os.path.exists(self.dbname)==False:
      self.connection=sqlite3.connect(self.dbname)
      self.cursor=self.connection.cursor()
      self.cursor.execute('CREATE TABLE destProfile' \
                          ' (ID        INTEGER NOT NULL PRIMARY KEY,' \
                          '  name      VARCHAR NOT NULL UNIQUE,' \
                          '  comment   VARCHAR,' \
                          '  size      INTEGER,' \
                          '  blocksize INTEGER,' \
                          '  addblock  INTEGER,' \
                          '  fldrname  VARCHAR,' \
                          '  final     INTEGER)')

      self.cursor.execute('CREATE TABLE baseProfile' \
                          ' (ID          INTEGER NOT NULL PRIMARY KEY,' \
                          '  name        VARCHAR NOT NULL UNIQUE,' \
                          '  comment     VARCHAR,' \
                          '  hiddenfiles INTEGER)')
      self.cursor.execute('CREATE TABLE folders' \
                          ' (ID        INTEGER NOT NULL PRIMARY KEY,' \
                          '  baseProID INTEGER NOT NULL,' \
                          '  name      VARCHAR)')

      self.connection.commit()
      self.__fillDefaults()
    else:
      self.connection=sqlite3.connect(self.dbname)
      self.cursor=self.connection.cursor()

  # ###########################################################
  # Stellt ein paar Default-Werte für Mediengrößen in die DB.
  def __fillDefaults(self):
    # def insertOrUpdateDest(self, name, comment, size, blocksize, addblock, folder, final):
    self.insertOrUpdateDest("RealCrypt BlueRay",      "FAT32 auf UDF1.02 (Nero4)",           24931450880,   8192, 0, HOMEDIR, 0)
    self.insertOrUpdateDest("DVD+R JolietRR",         "genisoimage ISO9660+JolietRR",         4700002304,   2048, 1, HOMEDIR, 1)
    self.insertOrUpdateDest("DVD+R UDF1.02",          "genisoimage ISO9660+UDF1.02",          4699518976,   2048, 2, HOMEDIR, 1)
    self.insertOrUpdateDest("DVD+R JolietRR+UDF1.02", "genisoimage ISO9660+JolietRR+UDF1.02", 4699506688,   2048, 3, HOMEDIR, 1)
    self.insertOrUpdateDest("DVD+R UDF2.01",          "truncate -s 4700372992 + mkudffs",     4698988544,   2048, 4, "/mnt",  1)

  # ###########################################################
  # Fügt einen Satz in "baseProfile" ein, die einzelnen
  # Ordnernamen werden in "folders" eingefügt und dem frisch
  # angelegten Satz in "baseProfile" zugeordnet.
  def insertOrUpdateBase(self, name, comment, inclHidden, folderList):
    self.cursor.execute('SELECT ID FROM baseProfile WHERE name LIKE ?', (name, ))
    c=self.cursor.fetchone() # c[0]=ID
    if c!=None:
      # Satz exitiert schon
      self.cursor.execute('UPDATE baseProfile SET comment=?, hiddenfiles=?' \
                          ' WHERE ID=?', (comment, inclHidden, c[0]))
      self.cursor.execute('DELETE FROM folders WHERE baseProID=?', (c[0], ))
      for folder in folderList:
        self.cursor.execute('INSERT INTO folders (baseProID, name) VALUES (?, ?)', (c[0], folder))
    else:
      # Satz neu anlegen
      self.cursor.execute('INSERT INTO baseProfile (name, comment, hiddenfiles)' \
                          ' VALUES (?, ?, ?)', (name, comment, inclHidden))
      self.connection.commit()
      self.cursor.execute('SELECT ID FROM baseProfile WHERE name=?', (name, ))
      c=self.cursor.fetchone() # c[0]=ID
      if c!=None:
        for folder in folderList:
          self.cursor.execute('INSERT INTO folders (baseProID, name) VALUES (?, ?)', (c[0], folder))
    self.connection.commit()

  # ###########################################################
  # Löscht den Satz, bei dem die Spalte(name) LIKE "name" ist.
  def deleteBase(self, name):
    self.cursor.execute('SELECT ID FROM baseProfile WHERE name LIKE ?', (name, ))
    c=self.cursor.fetchone()
    if c!=None:
      self.cursor.execute('DELETE FROM folders WHERE baseProID=?', (c[0], ))
      self.cursor.execute('DELETE FROM baseProfile WHERE ID=?', (c[0], ))
      self.connection.commit()

  # ###########################################################
  # Liefert alle Sätze aus "baseProfile" als Liste bzw. den
  # einen Satz, bei dem die Spalte(name) LIKE "name" ist.
  def getBaseProfiles(self, name="%"):
    self.cursor.execute('SELECT ID, name, comment, hiddenfiles FROM baseProfile' \
                        ' WHERE name LIKE ?', (name, ))
    rows1=self.cursor.fetchall()

    retlst=[]
    for r1 in rows1:
      self.cursor.execute('SELECT name FROM folders WHERE baseProID=?', (r1[0],))
      rows2=self.cursor.fetchall()
      fldrs=[]
      for r2 in rows2:
        fldrs.append(r2[0])
      retlst.append((r1[1], r1[2], r1[3], fldrs))
    return(retlst)

  # ###########################################################
  # Fügt einen Satz in "destProfile" ein.
  def insertOrUpdateDest(self, name, comment, size, blocksize, addblock, folder, final):
    self.cursor.execute('SELECT ID FROM destProfile WHERE name LIKE ?', (name, ))
    c=self.cursor.fetchone() # c[0]=ID
    if c!=None:
      # Satz exitiert schon
      self.cursor.execute('UPDATE destProfile' \
                          ' SET comment=?, size=?, blocksize=?, addblock=?, fldrname=?, final=?' \
                          ' WHERE ID=?', (comment, size, blocksize, addblock, folder, final, c[0]))
    else:
      self.cursor.execute('INSERT INTO destProfile (name, comment, size, blocksize, addblock, fldrname, final)' \
                          ' VALUES (?, ?, ?, ?, ?, ?, ?)', (name, comment, size, blocksize, addblock, folder, final))
    self.connection.commit()

  # ###########################################################
  # Löscht den Satz, bei dem die Spalte(name) LIKE "name" ist.
  def deleteDest(self, name):
    self.cursor.execute('DELETE FROM destProfile WHERE name like ?', (name, ))
    self.connection.commit()

  # ###########################################################
  # Liefert alle Sätze aus "destProfile" als Liste bzw. den
  # einen Satz, bei dem die Spalte(name) LIKE "name" ist.
  def getDestProfiles(self, name="%"):
    self.cursor.execute('SELECT name, comment, size, blocksize, addblock, fldrname, final FROM destProfile' \
                        ' WHERE name LIKE ?', (name, ))
    r=self.cursor.fetchall()
    return(r)

  # ###########################################################
  # Liefert alle Destination-Profile-Namen.
  def getDestProfileNames(self):
    self.cursor.execute('SELECT name FROM destProfile')
    r=self.cursor.fetchall()
    dpn=[]
    for r2 in r:
      dpn.append(r2[0])
    return(dpn)

  # ###########################################################
  # Liefert alle Source-Profile-Namen.
  def getBaseProfileNames(self):
    self.cursor.execute('SELECT name FROM baseProfile')
    r=self.cursor.fetchall()
    dpn=[]
    for r2 in r:
      dpn.append(r2[0])
    return(dpn)

