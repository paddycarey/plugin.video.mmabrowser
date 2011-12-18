#!/usr/bin/env python

import os
import socket
import sqlite3
import sys
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.utils import *
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
__thumbDir__          = os.path.join(__addondir__, 'thumbs')
__fighterDir__        = os.path.join(__addondir__, 'fighters')
__promotionDir__      = os.path.join(__addondir__, 'promotions')

def scanLibrary(scriptPath, libraryPath):

    if scriptPath == '/':
        ## scan libraryPath for directories containing sherdogEventID files
        log('Scanning library for event IDs/paths')
        cur.execute("DROP TABLE IF EXISTS library")
        cur.execute("CREATE TABLE library(ID TEXT, path TEXT)")
        library = []
        idFile = 'sherdogEventID'
        for x in os.walk(libraryPath):
            pathIdFile = os.path.join(x[0], idFile)
            if xbmcvfs.exists(pathIdFile):
                event = {}
                event['ID'] = open(pathIdFile).read()
                event['ID'] = event['ID'].replace('\n', '')
                event['path'] = x[0]
                log('Event ID/path found (%s): %s' % (event['ID'], event['path']))
                library.append(event)
                cur.execute('INSERT INTO library VALUES("%s", "%s")' % (event['ID'], event['path']))
        storageDB.commit()
    else:
        ## loading library from storage
        cur.execute("SELECT * FROM library")
        library = []
        for x in cur.fetchall():
            event = {}
            event['ID'] = x[0]
            event['path'] = x[1]
            library.append(event)
    return library

def allEvents():
    
    cur.execute("SELECT DISTINCT eventID, title, date FROM events ORDER BY date")
    for event in cur.fetchall():
        for x in libraryList:
            if event[0] == x['ID']:
                thumbPath = os.path.join(__thumbDir__, '%s-poster.jpg' % x['ID'])
                fanartPath = os.path.join(__thumbDir__, '%s-fanart.jpg' % x['ID'])
                addDir("%s: %s" % (event[2], event[1]), "/getEvent/%s" % event[0], 1, thumbPath, fanartPath)

def browseByOrganisation():

    cur.execute("SELECT DISTINCT promotion FROM events ORDER BY promotion")
    for promotion in cur.fetchall():
        promotionThumb = promotion[0] + '-poster.jpg'
        promotionFanart = promotion[0] + '-fanart.jpg'
        thumbPath = os.path.join(__promotionDir__, promotionThumb)
        fanartPath = os.path.join(__promotionDir__, promotionFanart)
        addDir(promotion[0], "/browsebyorganisation/%s" % promotion[0], 1, thumbPath, fanartPath)

def getEventsByOrganisation(organisation):

    cur.execute("SELECT eventID, title, date FROM events WHERE promotion='%s' ORDER BY date" % organisation)
    for event in cur.fetchall():
        for x in libraryList:
            if event[0] == x['ID']:
                thumbPath = os.path.join(__thumbDir__, '%s-poster.jpg' % x['ID'])
                fanartPath = os.path.join(__thumbDir__, '%s-fanart.jpg' % x['ID'])
                addDir("%s: %s" % (event[2], event[1]), "/getEvent/%s" % x['ID'], 1, thumbPath, fanartPath)

def browseByFighter():

    cur.execute("SELECT DISTINCT fighterID, name FROM fighters ORDER BY name")
    for fighter in cur.fetchall():
        fighterThumb = fighter[0] + '.jpg'
        thumbPath = os.path.join(__fighterDir__, fighterThumb)
        fanartPath = ''
        addDir(fighter[1], "/browsebyfighter/%s" % fighter[0], 1, thumbPath, fanartPath)

def getEventsByFighter(fighterID):

    cur.execute("SELECT DISTINCT eventID FROM fights WHERE (fighter1='%s' OR fighter2='%s')" % (fighterID, fighterID))
    events = []
    for eventID in cur.fetchall():
        eventDict = {}
        cur.execute("SELECT eventID, title, date FROM events WHERE eventID='%s'" % eventID)
        event = cur.fetchone()
        for x in libraryList:
            if x['ID'] == event[0]:
                eventDict['thumbPath'] = os.path.join(__thumbDir__, '%s-poster.jpg' % x['ID'])
                eventDict['fanartPath'] = os.path.join(__thumbDir__, '%s-fanart.jpg' % x['ID'])
                break
        eventDict['ID'] = event[0]
        eventDict['title'] = event[1]
        eventDict['date'] = event[2]
        events.append(eventDict)
    for event in sorted(events, key=lambda k: k['date']):
        addDir("%s: %s" % (event['date'], event['title']), "/getEvent/%s" % event['ID'], 1, event['thumbPath'], eventDict['fanartPath'])

def getEvent(eventID):
    
    cur.execute("SELECT * FROM events WHERE eventID='%s'" % eventID)
    event = cur.fetchone()
    for x in libraryList:
        if event[0] == x['ID']:
            thumbPath = os.path.join(__thumbDir__, '%s-poster.jpg' % x['ID'])
            fanartPath = os.path.join(__thumbDir__, '%s-fanart.jpg' % x['ID'])
            for root, dirs, files in os.walk(x['path']):
                for vidFile in files:
                    vidFileExt = os.path.splitext(vidFile)[1]
                    vidFilePath = os.path.join(root, vidFile)
                    if vidFileExt in ['.mkv', '.mp4', '.flv', '.avi']:
                        addLink(vidFile, '%s: %s, %s' % (event[3], event[4], event[5]), vidFilePath, thumbPath, fanartPath)
                    else:
                        log('File ignored: %s' % vidFilePath)

if (__name__ == "__main__"):

    ## parse plugin arguments
    params = get_params()

    ## get page number
    try:
        page = int(urllib.unquote_plus(params["page"]))
    except:
        page = 1

    ## get path
    try:
        path = urllib.unquote_plus(params["path"])
    except:
        path = "/"

    ## create directories needed for script operation
    for neededDir in [__addondir__, __thumbDir__, __fighterDir__, __promotionDir__]:
        xbmcvfs.mkdir(neededDir)

    ## initialise persistent storage
    storageDBPath = os.path.join(__addondir__, 'storage.db')
    storageDB = sqlite3.connect(storageDBPath)
    cur = storageDB.cursor()

    ## retrieve current list of events in libraryPath
    libraryList = scanLibrary(path, __addon__.getSetting("libraryPath"))

    try:
        ##attempt to load tables from storage
        cur.execute("SELECT * from events")
        cur.execute("SELECT * from fights")
        cur.execute("SELECT * from fighters")
    except sqlite3.Error, e:
        __addon__.setSetting(id="forceFullRescan", value='true')
        log('SQLite Error: %s' % e.args[0])
        log('Unable to load event list from storage: rescanning')
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
    for libraryItem in libraryList:
        scannedID = unicode(libraryItem['ID'])
        cur.execute("SELECT DISTINCT eventID FROM events")
        storedIDs = cur.fetchall()
        if not (scannedID,) in storedIDs:
            try:
                event = getEventDetails(libraryItem['ID'])
                cur.execute("INSERT INTO events VALUES('%s', '%s', '%s', '%s', '%s', '%s')" % (event['ID'], event['title'].replace('\'', ''), event['promotion'].replace('\'', ''), event['date'], event['venue'].replace('\'', ''), event['city'].replace('\'', '')))
                for fight in event['fights']:
                    cur.execute("INSERT INTO fights VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (event['ID'], fight['ID'], fight['fighter1'], fight['fighter2'], fight['winner'], fight['result'].replace('\'', ''), fight['round'].replace('\'', ''), fight['time'].replace('\'', '')))
                    cur.execute("SELECT fighterID from fighters")
                    fighters = cur.fetchall()
                    for fighter in [fight['fighter1'], fight['fighter2']]:
                        if not (fighter,) in fighters:
                            fighterDetails = getFighterDetails(fighter)
                            cur.execute("INSERT INTO fighters VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (fighterDetails['ID'], fighterDetails['name'].replace('\'', ''), fighterDetails['nickName'].replace('\'', ''), fighterDetails['association'].replace('\'', ''), fighterDetails['height'].replace('\'', ''), fighterDetails['weight'].replace('\'', ''), fighterDetails['birthYear'], fighterDetails['birthMonth'], fighterDetails['birthDay'], fighterDetails['city'].replace('\'', ''), fighterDetails['country'].replace('\'', '')))
                    storageDB.commit()
            except:
                print sys.exc_info()
                log('Error adding event to database: %s' % libraryItem['ID'])
                log('Rolling back database to clean state')
                storageDB.rollback()
                sys.exit(1)

    ## check path and generate desired list
    if path == "/":
        ## populate main menu
        addDir("Browse by: Organisation", "/browsebyorganisation/", 1, "", "")
        addDir("Browse by: Fighter", "/browsebyfighter/", 1, "", "")
        addDir("All Events", "/allevents/", 1, "", "")
    
    else:
        if path.startswith("/browsebyorganisation/"):
            log("path:%s" % path)
            organisation = path.replace('/browsebyorganisation/','')
            log("organisation:%s" % organisation)
            if organisation == '':
                ## populate list of organisations
                browseByOrganisation()
            else:
                ## populate list of events for a given organisation
                getEventsByOrganisation(organisation)
        elif path.startswith("/browsebyfighter/"):
            log("path:%s" % path)
            fighterID = path.replace('/browsebyfighter/','')
            log("fighterID:%s" % fighterID)
            if fighterID == '':
                ## populate list of fighters
                browseByFighter()
            else:
                ## populate list of all events a given fighter has fought in
                getEventsByFighter(fighterID)
        elif path == "/allevents/":
            ## populate list of all events
            allEvents()
        elif path.startswith("/getEvent/"):
            eventID = path.replace('/getEvent/','')
            ## populate list of all video files for a given event
            getEvent(eventID)

        ## add 'Next Page' button to bottom of list
        #addDir("> Next Page", path, page+1, "")

    ## close persistent storage file
    storageDB.close()
    ## finish adding items to list and display
    xbmcplugin.endOfDirectory(__addonidint__)
