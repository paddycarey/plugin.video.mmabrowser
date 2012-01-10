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
__thumbDir__          = os.path.join(__addondir__, 'events')
__fighterDir__        = os.path.join(__addondir__, 'fighters')
__fightDir__          = os.path.join(__addondir__, 'fights')
__promotionDir__      = os.path.join(__addondir__, 'promotions')

def scanLibrary(scriptPath, libraryPath):

    if scriptPath == '/':
        ## scan libraryPath for directories containing sherdogEventID files
        log('Scanning library for event IDs/paths')
        cur.execute("DROP TABLE IF EXISTS library")
        cur.execute("CREATE TABLE library(ID TEXT, path TEXT)")
        library = []
        idFiles = ['sherdogEventID', 'sherdogEventID.nfo']
        dirList = []
        for x in os.walk(libraryPath):
            dirList.append(x[0])
        dirCount = 0
        for x in dirList:
            dirCount = dirCount + 1
            dialog.update(int((dirCount / float(len(dirList))) * 100), "Scanning MMA Library for event ID files", x)
            for idFile in idFiles:
                pathIdFile = os.path.join(x, idFile)
                if xbmcvfs.exists(pathIdFile):
                    event = {}
                    event['ID'] = open(pathIdFile).read()
                    event['ID'] = event['ID'].replace('\n', '')
                    event['path'] = x
                    if not event['ID'] == '':
                        log('Event ID/path found (%s): %s' % (event['ID'], event['path']))
                        library.append(event)
                        cur.execute('INSERT INTO library VALUES("%s", "%s")' % (event['ID'], event['path']))
                    else:
                        log('Event ID file found but was empty : %s' % event['path'])
                    break
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
    
    cur.execute("SELECT DISTINCT eventID, title, promotion, date, venue, city FROM events ORDER BY date")
    for event in cur.fetchall():
        for x in libraryList:
            if event[0] == x['ID']:
                fightList = getFightersByEvent(event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList)

def browseByOrganisation():
    log('Browsing: Organisations')
    cur.execute("SELECT DISTINCT promotion FROM events ORDER BY promotion")
    for promotion in cur.fetchall():
        addPromotion(promotion[0])

def getEventsByOrganisation(organisation):
    log('Listing all events for: %s' % organisation)
    cur.execute("SELECT eventID, title, promotion, date, venue, city FROM events WHERE promotion='%s' ORDER BY date" % organisation)
    events = cur.fetchall()
    for event in events:
        for x in libraryList:
            if event[0] == x['ID']:
                fightList = getFightersByEvent(event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList)

def browseByFighter():

    cur.execute("SELECT DISTINCT * FROM fighters ORDER BY name")
    for fighter in cur.fetchall():
        addFighter(fighter[0], fighter[1], fighter[2], fighter[3], fighter[4], fighter[5], fighter[6], fighter[7], fighter[8], fighter[9], fighter[10])

def getEventsByFighter(fighterID):

    cur.execute("SELECT DISTINCT events.eventID, events.title, events.promotion, events.date, events.venue, events.city FROM events INNER JOIN fights ON events.eventID=fights.eventID WHERE (fighter1='%s' OR fighter2='%s') ORDER BY date" % (fighterID, fighterID))
    for event in cur.fetchall():
        for x in libraryList:
            if event[0] == x['ID']:
                fightList = getFightersByEvent(event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList)

def getFightersByEvent(eventID):
    cur.execute("SELECT fightID, fighter1, fighter2 FROM fights WHERE eventID='%s' ORDER BY fightID" % eventID)
    fightList = []
    fightListProcessed = []
    while True:
        fight = cur.fetchone()
        if fight == None:
            break
        fightList.append(fight)
    for fNum, fighter1, fighter2 in fightList:
        cur.execute("SELECT name FROM fighters WHERE fighterID='%s'" % fighter1)
        f1 = cur.fetchone()
        cur.execute("SELECT name FROM fighters WHERE fighterID='%s'" % fighter2)
        f2 = cur.fetchone()
        fight = (fNum, f1[0], f2[0])
        fightListProcessed.append(fight)
    return fightListProcessed

def searchAll():
    searchStr = getUserInput(title = "Search MMA Library")
    log("Searching for: %s" % searchStr)
    cur.execute("SELECT DISTINCT eventID, title, promotion, date, venue, city FROM events WHERE (eventID LIKE '%s' OR title LIKE '%s' OR promotion LIKE '%s' OR date LIKE '%s' OR venue LIKE '%s' OR city LIKE '%s') ORDER BY date" % ("%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%"))
    for event in cur.fetchall():
        for x in libraryList:
            if event[0] == x['ID']:
                fightList = getFightersByEvent(event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList)
    cur.execute("SELECT DISTINCT * FROM fighters WHERE (fighterID LIKE '%s' OR name LIKE '%s' OR nickname LIKE '%s' OR association LIKE '%s' OR city LIKE '%s' OR country LIKE '%s') ORDER BY name" % ("%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%"))
    for fighter in cur.fetchall():
        addFighter(fighter[0], fighter[1], fighter[2], fighter[3], fighter[4], fighter[5], fighter[6], fighter[7], fighter[8], fighter[9], fighter[10])

def getEvent(eventID):
    
    cur.execute("SELECT * FROM events WHERE eventID='%s'" % eventID)
    event = cur.fetchone()
    for x in libraryList:
        if event[0] == x['ID']:
            thumbPath = os.path.join(__thumbDir__, '%s-poster.jpg' % x['ID'])
            if not xbmcvfs.exists(thumbPath):
                thumbPath = os.path.join(__promotionDir__, '%s-poster.jpg' % event[2].replace(' ', ''))
            fanartPath = os.path.join(__thumbDir__, '%s-fanart.jpg' % x['ID'])
            if not xbmcvfs.exists(fanartPath):
                fanartPath = os.path.join(__promotionDir__, '%s-fanart.jpg' % event[2].replace(' ', ''))
            outline = '%s: %s, %s' % (event[3], event[4], event[5])
            try:
                description = open(os.path.join(__thumbDir__, '%s-description.txt' % event[0])).read()
            except IOError:
                description = outline
            fileList = []
            for root, dirs, files in os.walk(x['path']):
                for vidFileName in files:
                    vidFile = {}
                    vidFile['filename'] = vidFileName
                    vidFile['ext'] = os.path.splitext(vidFileName)[1]
                    vidFile['path'] = os.path.join(root, vidFileName)
                    if __addon__.getSetting("cleanFilenames") == 'true':
                        vidFile['title'] = os.path.splitext(vidFileName)[0].lstrip('0123456789. ')
                    else:
                        vidFile['title'] = vidFileName
                    if vidFile['ext'] in ['.mkv', '.mp4', '.flv', '.avi', '.iso', '.mpg', '.ts']:
                        fileList.append(vidFile)
                    else:
                        log('File ignored: %s' % vidFile['path'])
            if len(fileList) == 1:
                xbmc.Player().play(fileList[0]['path'])
                sys.exit(0)
            else:
                for vidFile in sorted(fileList, key=lambda k: k['filename']):
                    addLink(linkName = vidFile['title'], plotoutline = outline, plot = description, url = vidFile['path'], thumbPath = thumbPath, fanartPath = fanartPath, genre = 'MMA')

if (__name__ == "__main__"):

    xbmcplugin.setContent(__addonidint__, 'tvshows') 

    ## parse plugin arguments
    params = get_params()

    ## get path
    try:
        path = urllib.unquote_plus(params["path"])
    except:
        path = "/"

    log('Script path: %s' % path)

    ## create directories needed for script operation
    for neededDir in [__addondir__, __thumbDir__, __fighterDir__, __fightDir__, __promotionDir__]:
        xbmcvfs.mkdir(neededDir)

    ## initialise persistent storage
    storageDBPath = os.path.join(__addondir__, 'storage.db')
    storageDB = sqlite3.connect(storageDBPath)
    cur = storageDB.cursor()

    if path == '/':
        dialog = xbmcgui.DialogProgress()
        dialog.create(__addonname__, "MMA Browser", "Loading")

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
    cur.execute("SELECT DISTINCT eventID FROM events")
    storedIDs = cur.fetchall()
    libItemCount = 0
    for libraryItem in libraryList:
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
                dialog.close()
                sys.exit(1)

    if path == '/':
        dialog.close()

    ## check path and generate desired list
    if path == "/":
        if __addon__.getSetting("checkMissingExtras") == 'true':
            getMissingExtras()
        ## populate main menu
        addDir("Browse by: Organisation", "/browsebyorganisation/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Browse a list of all MMA Promotions in your library.")
        addDir("Browse by: Fighter", "/browsebyfighter/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Browse a list of all fighters in your library")
        addDir("All Events", "/allevents/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Browse a list of all events in your library")
        addDir("Search", "/search/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Search all items in your library")
    else:
        if path.startswith("/browsebyorganisation"):
            log("path:%s" % path)
            organisation = path.replace('/browsebyorganisation','')
            log("organisation:%s" % organisation)
            if organisation == '':
                ## populate list of organisations
                browseByOrganisation()
            else:
                ## populate list of events for a given organisation
                getEventsByOrganisation(organisation.lstrip('/'))
        elif path.startswith("/browsebyfighter"):
            log("path:%s" % path)
            fighterID = path.replace('/browsebyfighter','')
            log("fighterID:%s" % fighterID)
            if fighterID == '':
                ## populate list of fighters
                browseByFighter()
            else:
                ## populate list of all events a given fighter has fought in
                getEventsByFighter(fighterID.lstrip('/'))
        elif path == "/allevents":
            ## populate list of all events
            allEvents()
        elif path == "/search":
            ## populate list of all events
            searchAll()
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
