#!/usr/bin/env python

import os
import socket
import sqlite3
import sys
import traceback
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

# Use json instead of simplejson when python v2.7 or greater
if sys.version_info < (2, 7):
     import json as simplejson
else:
     import simplejson

# import necessary functions
from resources.lib.utils import *
from resources.lib.sherdog import *
from resources.lib.dbInterface import getData, setData

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

dialog = xbmcgui.DialogProgress()


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
            log('Checking for directories in: %s' % dirName)
            json_response = xbmc.executeJSONRPC('{ "jsonrpc" : "2.0" , "method" : "Files.GetDirectory" , "params" : { "directory" : "%s" , "sort" : { "method" : "file" } } , "id" : 1 }' % dirName.encode('utf-8').replace('\\', '\\\\'))
            jsonobject = simplejson.loads(json_response)
            if jsonobject['result']['files']:
                for item in jsonobject['result']['files']:
                    if item['filetype'] == 'directory':
                        currentLevelDirList.append(item['file'])
    return dirList


def getFileList(path):
    fileList = []
    dirList = getDirList(path)
    for dirName in dirList:
        log('Checking for files in: %s' % dirName)
        json_response = xbmc.executeJSONRPC('{ "jsonrpc" : "2.0" , "method" : "Files.GetDirectory" , "params" : { "directory" : "%s" , "sort" : { "method" : "file" } , "media" : "video" } , "id" : 1 }' % dirName.encode('utf-8').replace('\\', '\\\\'))
        jsonobject = simplejson.loads(json_response)
        if jsonobject['result']['files']:
            for item in jsonobject['result']['files']:
                if item['filetype'] == 'file':
                    fileList.append(item['file'])
                    log('Found video: %s' % item['file'])
    return fileList


def getMissingExtras():
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


def scanLibrary():
    ## scan libraryPath for directories containing sherdogEventID files
    log('Scanning library for event IDs/paths')
    setData("DROP TABLE IF EXISTS library")
    setData("CREATE TABLE library(ID TEXT, path TEXT)")
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
                        setData('INSERT INTO library VALUES("%s", "%s")' % (event['ID'], event['path']))
                    else:
                        log('Event ID file found but was empty : %s' % event['path'])
                    break


def loadLibrary():
    library = []
    for x in getData("SELECT * FROM library"):
        event = {}
        event['ID'] = x[0]
        event['path'] = x[1]
        library.append(event)
    return library


def initLibrary():
    try:
        ##attempt to load tables from db
        getData("SELECT * from events")
        getData("SELECT * from fights")
        getData("SELECT * from fighters")
    except sqlite3.Error, e:
        __addon__.setSetting(id="forceFullRescan", value='true')
        log('SQLite Error: %s' % e.args[0])
        log('Unable to load tables from database: rescanning')
        log('Performing full event scan: THIS MAY TAKE A VERY LONG TIME', xbmc.LOGWARNING)
    if __addon__.getSetting("forceFullRescan") == 'true':
        setData("DROP TABLE IF EXISTS events")
        setData("CREATE TABLE events(eventID TEXT PRIMARY KEY, title TEXT, promotion TEXT, date TEXT, venue TEXT, city TEXT, fightList TEXT)")
        setData("DROP TABLE IF EXISTS fighters")
        setData("CREATE TABLE fighters(fighterID TEXT PRIMARY KEY, name TEXT, nickName TEXT, association TEXT, height TEXT, weight TEXT, birthDate TEXT, city TEXT, country TEXT, thumbURL TEXT)")
        setData("DROP TABLE IF EXISTS fights")
        setData("CREATE TABLE fights(eventID TEXT, fighterID TEXT, PRIMARY KEY (eventID, fighterID))")
        __addon__.setSetting(id="forceFullRescan", value='false')


def getMissingEvents():

    eventCount = 1

    # retrieve list of already scanned events
    storedIDList = getData("SELECT DISTINCT eventID FROM events")
    storedIDs = []
    for x in storedIDList:
        storedIDs.append(x['eventID'])

    # retrieve list of all events
    libraryList = loadLibrary()
    libraryIDs = []
    for x in libraryList:
        libraryIDs.append(x['ID'])
    
    # retrieve list of events that need to be scanned
    unscannedEvents = []
    for event in libraryIDs:
        if not event in storedIDs:
            unscannedEvents.append(event)

    for eventID in unscannedEvents:
        dialog.update(int((eventCount / float(len(unscannedEvents))) * 100), "Retrieving event details from Sherdog.com", "ID: %s" % eventID)
        log('Retrieving event details from sherdog.com: %s' % eventID)
        event = getEventDetails(int(eventID))
        log('Event ID:       %s' % event['ID'])
        log('Event Title:    %s' % event['title'].replace('\'', ''))
        log('Event Promoter: %s' % event['promotion'].replace('\'', ''))
        log('Event Date:     %s' % event['date'])
        log('Event Venue:    %s' % event['venue'].replace('\'', ''))
        log('Event City:     %s' % event['city'].replace('\'', ''))
        eventTuple = (  event['ID'],
                        event['title'].replace('\'', ''),
                        event['promotion'].replace('\'', ''),
                        event['date'], event['venue'].replace('\'', ''),
                        event['city'].replace('\'', ''),
                        event['fights'].replace('\'', ''))
        # execute sql to add data to dataset
        if setData("INSERT INTO events VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % eventTuple, deferCommit = True):
            for fighter in event['fighters']:
                if not setData("INSERT INTO fights VALUES('%s', '%s')" % (event['ID'], fighter), deferCommit = True):
                    break
            log('Retrieved event details from sherdog.com: %s' % eventID)
            # committing event to database
            setData()
        else:
            log('Error Retrieving event details from sherdog.com: %s' % eventID)
        eventCount = eventCount + 1


def getMissingFighters():
    
    fighterCount = 1
    
    # get list of already scanned fighters
    scannedFighterList = getData("SELECT fighterID from fighters")
    scannedFighters = []
    for x in scannedFighterList:
        scannedFighters.append(x['fighterID'])

    # get list of all fighters (scanned and unscanned)
    allFighterList = getData("SELECT DISTINCT fighterID from fights")
    allFighters = []
    for x in allFighterList:
        allFighters.append(x['fighterID'])

    # get list of fighters that need to be scraped
    unscannedFighters = []
    for fighter in allFighters:
        if not fighter in scannedFighters:
            unscannedFighters.append(fighter)

    # scrape data for fighters in unscanned list
    for fighter in unscannedFighters:
        
        # update onscreen progress dialog
        dialog.update(int((fighterCount / float(len(unscannedFighters))) * 100), "Retrieving fighter details from Sherdog.com", "ID: %s" % fighter, "")
        # print status to log
        log('## Retrieving fighter details from sherdog.com: %s' % fighter)
        
        # retrieve fighter details from sherdog.com
        fighterDetails = getFighterDetails(int(fighter))
        
        # print fighter details to log
        log('Fighter ID:       %s' % fighterDetails['ID'])
        log('Fighter Name:     %s' % fighterDetails['name'].replace('\'', ''))
        log('Fighter Nickname: %s' % fighterDetails['nickName'].replace('\'', ''))
        log('Fighter Assoc.:   %s' % fighterDetails['association'].replace('\'', ''))
        log('Fighter Height:   %s' % fighterDetails['height'].replace('\'', ''))
        log('fighter Weight:   %s' % fighterDetails['weight'].replace('\'', ''))
        log('Fighter D.O.B.:   %s' % fighterDetails['birthDate'])
        log('Fighter City:     %s' % fighterDetails['city'].replace('\'', ''))
        log('Fighter Country:  %s' % fighterDetails['country'].replace('\'', ''))
        log('Fighter Image:    %s' % fighterDetails['thumbUrl'])
        
        # construct tuple of arguments for use in constructing sql query
        fighterTuple = (fighterDetails['ID'], 
                        fighterDetails['name'].replace('\'', ''),
                        fighterDetails['nickName'].replace('\'', ''),
                        fighterDetails['association'].replace('\'', ''),
                        fighterDetails['height'].replace('\'', ''),
                        fighterDetails['weight'].replace('\'', ''),
                        fighterDetails['birthDate'],
                        fighterDetails['city'].replace('\'', ''),
                        fighterDetails['country'].replace('\'', ''),
                        fighterDetails['thumbUrl'])
        
        # perform sql query
        setData("INSERT INTO fighters VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % fighterTuple)
        
        # increment fighter count
        fighterCount = fighterCount + 1


def getEvents(promotion = '', fighterID = '', searchStr = '', eventID = ''):

    # get events by promotion
    if not promotion == '':
        return getData("SELECT * FROM events WHERE promotion='%s' ORDER BY date" % promotion)
    # get events by fighter
    elif not fighterID == '':
        return getData("SELECT events.* FROM events INNER JOIN fights ON events.eventID=fights.eventID WHERE fighterID='%s' ORDER BY date" % fighterID)
    # search events
    elif not searchStr == '':
        return getData("SELECT * FROM events WHERE (eventID LIKE '%s' OR title LIKE '%s' OR promotion LIKE '%s' OR date LIKE '%s' OR venue LIKE '%s' OR city LIKE '%s') ORDER BY date" % ("%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%"))
    # get single event details
    elif not eventID == '':
        return getData("SELECT * FROM events WHERE eventID='%s'" % eventID)
    # show all events
    else:
        return getData("SELECT * FROM events")


def getFighters(searchStr = ''):
    
    # search fighters
    if not searchStr == '':
        return getData("SELECT DISTINCT fighters.*, COUNT(*) AS cnt FROM fighters INNER JOIN fights ON (fights.fighterID=fighters.fighterID) WHERE (fighters.fighterID LIKE '%s' OR fighters.name LIKE '%s' OR fighters.nickname LIKE '%s' OR fighters.association LIKE '%s' OR fighters.city LIKE '%s' OR fighters.country LIKE '%s') GROUP BY fighters.fighterID ORDER BY fighters.name" % ("%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%"))
    # show all fighters
    else:
        return getData("SELECT DISTINCT fighters.*, COUNT(*) AS cnt FROM fighters INNER JOIN fights ON (fights.fighterID=fighters.fighterID) GROUP BY fighters.fighterID ORDER BY fighters.name")


def getPromotions():

    # get all promotions
    return getData("SELECT DISTINCT promotion FROM events ORDER BY promotion")


def getCounts(promotion = '', fighterID = ''):
    
    # get count of events by promotion
    if not promotion == '':
        return getData("SELECT COUNT(eventID) AS cnt FROM events WHERE promotion='%s'" % promotion)
    # get count of events by promotion
    elif not fighterID == '':
        return getData("SELECT COUNT(eventID) AS cnt FROM fights WHERE fighterID='%s'" % fighterID)
