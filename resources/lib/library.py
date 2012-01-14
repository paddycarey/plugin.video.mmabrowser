#!/usr/bin/env python

import os
import simplejson
import socket
import sqlite3
import sys
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

import resources.lib.databaseops as dbops
from resources.lib.utils import log
from resources.lib.sherdog import *

### get addon info
__addon__             = xbmcaddon.Addon()
__addonid__           = __addon__.getAddonInfo('id')
__addonidint__        = int(sys.argv[1])
__addonname__         = __addon__.getAddonInfo('name')
__author__            = __addon__.getAddonInfo('author')
__version__           = __addon__.getAddonInfo('version')
__localize__          = __addon__.getLocalizedString
__addonpath__         = __addon__.getAddonInfo('path')
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__thumbDir__          = os.path.join(__addondir__, 'events')
__fighterDir__        = os.path.join(__addondir__, 'fighters')
__fightDir__          = os.path.join(__addondir__, 'fights')
__promotionDir__      = os.path.join(__addondir__, 'promotions')
__artBaseURL__        = "http://mmaartwork.wackwack.co.uk/"

forceFullRescan = __addon__.getSetting("forceFullRescan") == 'true'

## initialise database
storageDBPath = os.path.join(__addondir__, 'storage.db')
storageDB = sqlite3.connect(storageDBPath)

def getDirList(path):
    dirList = []
    currentLevelDirList = [path]
    while True:
        prevLevelDirList = []
        if len(currentLevelDirList) > 0:
            for dirName in currentLevelDirList:
                prevLevelDirList.append(dirName)
                dirList.append(dirName)
            currentLevelDirList = []
        else:
            break
        for dirName in prevLevelDirList:
            log('Checking for directories in: %s' % dirName.encode('utf-8'))
            json_response = xbmc.executeJSONRPC('{ "jsonrpc" : "2.0" , "method" : "Files.GetDirectory" , "params" : { "directory" : "%s" , "sort" : { "method" : "file" } } , "id" : 1 }' % dirName.encode('utf-8'))
            log('json_response: %s' % json_response)
            jsonobject = simplejson.loads(json_response)
            if jsonobject['result']['files']:
                for item in jsonobject['result']['files']:
                    if item['filetype'] == 'directory':
                        currentLevelDirList.append(item['file'])
                        log('Found directory: %s' % item['file'])
    return dirList

def getFileList(path):
    fileList = []
    dirList = getDirList(path)
    for dirName in dirList:
        log('Checking for files in: %s' % dirName.encode('utf-8'))
        json_response = xbmc.executeJSONRPC('{ "jsonrpc" : "2.0" , "method" : "Files.GetDirectory" , "params" : { "directory" : "%s" , "sort" : { "method" : "file" } , "media" : "video" } , "id" : 1 }' % dirName.encode('utf-8'))
        log('json_response: %s' % json_response)
        jsonobject = simplejson.loads(json_response)
        if jsonobject['result']['files']:
            for item in jsonobject['result']['files']:
                if item['filetype'] == 'file':
                    fileList.append(item['file'])
                    log('Found video: %s' % item['file'])
    return fileList

def getMissingExtras():
    dialog = xbmcgui.DialogProgress()
    dialog.create(__addonname__, "MMA Browser", "Loading")
    if downloadFile(__artBaseURL__ + "repolist.txt", os.path.join(__addondir__, 'repolist.txt')):
        availableExtraList = []
        for availableExtra in open(os.path.join(__addondir__, 'repolist.txt')).readlines():
            availableExtraList.append(availableExtra)
        totalExtras = len(availableExtraList)
        extraCount = 0
        for availableExtra in availableExtraList:
            extraCount = extraCount + 1
            extraType = availableExtra.split('/', 1)[0]
            extraFilename = availableExtra.split('/', 1)[1].strip()
            dialog.update(int((extraCount / float(totalExtras)) * 100), "Downloading artwork/metadata", extraFilename)
            if not xbmcvfs.exists(os.path.join(__addondir__, extraType, extraFilename)):
                downloadFile(__artBaseURL__ + availableExtra, os.path.join(__addondir__, extraType, extraFilename))
    dialog.close()

def scanLibrary():
    dialog = xbmcgui.DialogProgress()
    dialog.create(__addonname__, "MMA Browser", "Loading")
    ## scan libraryPath for directories containing sherdogEventID files
    log('Scanning library for event IDs/paths')
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("DROP TABLE IF EXISTS library")
        cur.execute("CREATE TABLE library(ID TEXT, path TEXT)")
        idFiles = ['sherdogEventID', 'sherdogEventID.nfo']
        dirList = []
        dirList = getDirList(__addon__.getSetting("libraryPath"))
        dirCount = 0
        for x in dirList:
            if not dialog.iscanceled():
                dirCount = dirCount + 1
                dialog.update(int((dirCount / float(len(dirList))) * 100), "Scanning MMA Library for event ID files", x)
                for idFile in idFiles:
                    pathIdFile = os.path.join(x, idFile)
                    if xbmcvfs.exists(pathIdFile):
                        event = {}
                        try:
                            event['ID'] = open(pathIdFile).read()
                        except IOError:
                            tmpID = os.path.join(__addondir__, 'tmpID')
                            if xbmcvfs.copy(pathIdFile, tmpID):
                                event['ID'] = open(tmpID).read()
                                xbmcvfs.delete(tmpID)
                            else:
                                event['ID'] = ''
                        event['ID'] = event['ID'].replace('\n', '')
                        event['path'] = x
                        if not event['ID'] == '':
                            log('Event ID/path found (%s): %s' % (event['ID'], event['path']))
                            cur.execute('INSERT INTO library VALUES("%s", "%s")' % (event['ID'], event['path']))
                        else:
                            log('Event ID file found but was empty : %s' % event['path'])
                        break
    dialog.close()

def loadLibrary():
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("SELECT * FROM library")
        library = []
        for x in cur.fetchall():
            event = {}
            event['ID'] = x[0]
            event['path'] = x[1]
            library.append(event)
    return library

def getMissingData():
    dialog = xbmcgui.DialogProgress()
    dialog.create(__addonname__, "MMA Browser", "Loading")
    with storageDB:
        cur = storageDB.cursor()
        try:
            ##attempt to load tables from db
            cur.execute("SELECT * from events")
            cur.execute("SELECT * from fights")
            cur.execute("SELECT * from fighters")
        except sqlite3.Error, e:
            __addon__.setSetting(id="forceFullRescan", value='true')
            log('SQLite Error: %s' % e.args[0])
            log('Unable to load tables from database: rescanning')
            log('Performing full event scan: THIS MAY TAKE A VERY LONG TIME', xbmc.LOGWARNING)
        if __addon__.getSetting("forceFullRescan") == 'true':
            cur.execute("DROP TABLE IF EXISTS events")
            cur.execute("CREATE TABLE events(eventID TEXT, title TEXT, promotion TEXT, date TEXT, venue TEXT, city TEXT)")
            cur.execute("DROP TABLE IF EXISTS fights")
            cur.execute("CREATE TABLE fights(eventID TEXT, fightID TEXT, fighter1 TEXT, fighter2 TEXT, winner TEXT, result TEXT, round TEXT, time TEXT)")
            cur.execute("DROP TABLE IF EXISTS fighters")
            cur.execute("CREATE TABLE fighters(fighterID TEXT, name TEXT, nickName TEXT, association TEXT, height TEXT, weight TEXT, birthYear TEXT, birthMonth TEXT, birthDay TEXT, city TEXT, country TEXT)")
            __addon__.setSetting(id="forceFullRescan", value='false')

    
        ## for every new event in library retrieve details from sherdog.com
        cur.execute("SELECT DISTINCT eventID FROM events")
        storedIDs = cur.fetchall()
        libItemCount = 0
        libraryList = loadLibrary()
        for libraryItem in libraryList:
            if not dialog.iscanceled():
                libItemCount = libItemCount + 1
                scannedID = unicode(libraryItem['ID'])
                if not (scannedID,) in storedIDs:
                    try:
                        dialog.update(int((libItemCount / float(len(libraryList))) * 100), "Retrieving event details from Sherdog.com", "ID: %s" % libraryItem['ID'], "Path: %s" % libraryItem['path'])
                        event = getEventDetails(libraryItem['ID'])
                        cur.execute("INSERT INTO events VALUES('%s', '%s', '%s', '%s', '%s', '%s')" % (event['ID'], event['title'].replace('\'', ''), event['promotion'].replace('\'', ''), event['date'], event['venue'].replace('\'', ''), event['city'].replace('\'', '')))
                        for fight in event['fights']:
                            cur.execute("INSERT INTO fights VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (event['ID'], fight['ID'], fight['fighter1'], fight['fighter2'], fight['winner'], fight['result'].replace('\'', ''), fight['round'].replace('\'', ''), fight['time'].replace('\'', '')))
                            cur.execute("SELECT fighterID from fighters")
                            fighters = cur.fetchall()
                            for fighter in [fight['fighter1'], fight['fighter2']]:
                                if not (fighter,) in fighters:
                                    dialog.update(int((libItemCount / float(len(libraryList))) * 100), "Retrieving fighter details from Sherdog.com", "ID: %s" % fighter, "")
                                    fighterDetails = getFighterDetails(fighter)
                                    cur.execute("INSERT INTO fighters VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (fighterDetails['ID'], fighterDetails['name'].replace('\'', ''), fighterDetails['nickName'].replace('\'', ''), fighterDetails['association'].replace('\'', ''), fighterDetails['height'].replace('\'', ''), fighterDetails['weight'].replace('\'', ''), fighterDetails['birthYear'], fighterDetails['birthMonth'], fighterDetails['birthDay'], fighterDetails['city'].replace('\'', ''), fighterDetails['country'].replace('\'', '')))
                            storageDB.commit()
                    except:
                        print sys.exc_info()
                        log('Error adding event to database: %s' % libraryItem['ID'])
                        log('Rolling back database to clean state')
                        storageDB.rollback()
                        sys.exit(1)
    dialog.close()
