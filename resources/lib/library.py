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

## import necessary functions
from resources.lib.utils import getDirList, getFileList, log
from resources.lib.sherdog import getEventDetails, getFighterDetails
from resources.lib.dbInterface import getData, setData

## get addon info
__addon__             = xbmcaddon.Addon()
__addonname__         = __addon__.getAddonInfo('name')
__localize__          = __addon__.getLocalizedString
__addonpath__         = __addon__.getAddonInfo('path')
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('profile'))

## get artwork directories
__thumbDir__          = os.path.join(__addondir__, 'events')
__fighterDir__        = os.path.join(__addondir__, 'fighters')
__promotionDir__      = os.path.join(__addondir__, 'promotions')
__repoURL__        = "http://mmaartwork.wackwack.co.uk/"

## initialise progress dialog
dialogProgress = xbmcgui.DialogProgress()


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


def updateLibrary():

    ## print message to log
    log('Updating Library')
    
    ## possible filenames for event ID files (subject to change)
    idFiles = ['event.nfo', 'sherdogEventID.nfo', 'sherdogEventID']
   
    ## check if user has requested full rescan
    if __addon__.getSetting("forceFullRescan") == 'true':
        
        ## drop all tables if user has selected full rescan
        setData("DROP TABLE IF EXISTS events")
        setData("DROP TABLE IF EXISTS fighters")
        setData("DROP TABLE IF EXISTS fights")
        
        ## set setting to false after dropping tables
        __addon__.setSetting(id="forceFullRescan", value='false')
        
    ## create metadata tables in database if they don't exist
    setData("CREATE TABLE IF NOT EXISTS fights(eventID TEXT, fighterID TEXT, PRIMARY KEY (eventID, fighterID))")
    setData("CREATE TABLE IF NOT EXISTS events(eventID TEXT PRIMARY KEY, title TEXT, promotion TEXT, date TEXT, venue TEXT, city TEXT, fightList TEXT)")
    setData("CREATE TABLE IF NOT EXISTS fighters(fighterID TEXT PRIMARY KEY, name TEXT, nickName TEXT, association TEXT, height TEXT, weight TEXT, birthDate TEXT, city TEXT, country TEXT, thumbURL TEXT)")
    
    ## drop and recreate library (IDs, paths) table
    setData("DROP TABLE IF EXISTS library")
    setData("CREATE TABLE library(ID TEXT, path TEXT)")
    
    ## show progress dialog
    dialogProgress.create(__addonname__, __localize__(32026))
    
    ## set count of found directories to 0
    dirCount = 0
    
    ## find all directories in configured library path
    dirList = getDirList(__addon__.getSetting("libraryPath"))
    
    ## loop over all directories in configured library path
    for directory in dirList:
        
        ## check if user has pressed cancel
        if not dialogProgress.iscanceled():
            
            ## increment directory count
            dirCount += 1
            
            ## update progress dialog
            dialogProgress.update(int((dirCount / float(len(dirList))) * 100), __localize__(32031), directory, '')
            
            ## loop over possible filenames for event ID files (soon to be removed)
            for idFile in idFiles:
                
                ## construct path to ID file
                pathIdFile = os.path.join(directory, idFile)
                
                ## check if ID file exists
                if xbmcvfs.exists(pathIdFile):

                    try:
                        
                        ## attempt to open ID file and read ID
                        eventID = open(pathIdFile).read()
                    
                    except IOError:
                        
                        ## copy ID file locally if unable to open
                        tmpID = os.path.join(__addondir__, 'tmpID')
                        
                        if xbmcvfs.copy(pathIdFile, tmpID):
                            
                            ## attempt to open ID file and read ID
                            eventID = open(tmpID).read()
                            
                            ## delete temporary file
                            xbmcvfs.delete(tmpID)
                            
                        else:
                            
                            ## set ID to empty string if unable to read ID file
                            eventID = ''
                    
                    ## strip any newlines or whitespace from ID
                    eventID = eventID.strip()
                    
                    ## check that ID is not blank
                    if eventID == '':
                        
                        ## print error to log
                        log('Event ID file found but was empty : %s' % directory, xbmc.LOGERROR)
                        
                    else:
                        
                        ## print details of found event to log
                        log('Event ID/path found (%s): %s' % (eventID, directory))
                        
                        ## insert event ID and path into library table
                        setData('INSERT INTO library VALUES("%s", "%s")' % (eventID, directory))
                        
                        ## stop checking for ID file if ID found
                        break
    
    ## set event count to 1
    eventCount = 1
    
    ## get list of unscanned event IDs
    unscannedEvents = getMissingEvents()
    
    ## loop over list of unscanned events
    for eventID in unscannedEvents:

        ## check if user has pressed cancel
        if not dialogProgress.iscanceled():

            ## update progress dialog
            dialogPercentage = int((eventCount / float(len(unscannedEvents))) * 100)
            line1 = __localize__(32027)
            line2 = '%s: %s' % (__localize__(32028), eventID)
            line3 = ''
            dialogProgress.update(dialogPercentage, line1, line2, line3)
            
            ## scrape event and add to databse
            scanEvent(eventID)
            
            ## increment event count
            eventCount += 1
    
    ## set fighter count to 1
    fighterCount = 1

    ## get list of unscanned event IDs
    unscannedFighters = getMissingFighters()

    ## loop over list of unscanned fighter IDs
    for fighter in unscannedFighters:
        
        ## check if user has pressed cancel
        if not dialogProgress.iscanceled():
            
            # update onscreen progress dialog
            dialogPercentage = int((fighterCount / float(len(unscannedFighters))) * 100)
            line1 = __localize__(32029)
            line2 = '%s: %s' % (__localize__(32030), fighter)
            line3 = ''
            dialogProgress.update(dialogPercentage, line1, line2, line3)
    
            ## scrape event and add to databse
            scanFighter(fighter)
            
            ## increment event count
            fighterCount += 1
    
    ## close progress dialog
    dialogProgress.close()


def getMissingEvents():

    # retrieve list of already scanned events
    storedIDList = getData("SELECT DISTINCT eventID FROM events")
    storedIDs = []
    for x in storedIDList:
        storedIDs.append(x['eventID'])

    # retrieve list of all events
    libraryList = getData("SELECT DISTINCT * FROM library")
    libraryIDs = []
    for x in libraryList:
        libraryIDs.append(x['ID'])
    
    # retrieve list of events that need to be scanned
    unscannedEvents = []
    for event in libraryIDs:
        if not event in storedIDs:
            unscannedEvents.append(event)
    
    ## return list of IDs of all events which have not yet been scanned
    return unscannedEvents


def getMissingFighters():
        
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
    
    ## return list of unscanned fighter IDs
    return unscannedFighters


def scanEvent(eventID):

    ## print status to log
    log('Retrieving event details from sherdog.com: %s' % eventID)
    
    ## scrape evnt details from sherdog
    event = getEventDetails(int(eventID))
    
    ## print event details to log
    log('Event ID:       %s' % event['ID'])
    log('Event Title:    %s' % event['title'].replace('\'', ''))
    log('Event Promoter: %s' % event['promotion'].replace('\'', ''))
    log('Event Date:     %s' % event['date'])
    log('Event Venue:    %s' % event['venue'].replace('\'', ''))
    log('Event City:     %s' % event['city'].replace('\'', ''))
    
    ## construct tuple of arguments to pass to sql statement
    eventTuple = (  event['ID'],
                    event['title'].replace('\'', ''),
                    event['promotion'].replace('\'', ''),
                    event['date'], event['venue'].replace('\'', ''),
                    event['city'].replace('\'', ''),
                    event['fights'].replace('\'', ''))
    
    ## execute sql to add data to dataset
    if setData("INSERT INTO events VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % eventTuple, deferCommit = True):
        
        ## loop over all fighters on event
        for fighter in event['fighters']:
            
            ## insert fight record into fights table
            if not setData("INSERT INTO fights VALUES('%s', '%s')" % (event['ID'], fighter), deferCommit = True):
                
                ## break if unable to add to database
                break
        
        ## print success to log
        log('Retrieved event details from sherdog.com: %s' % eventID)
        
        # commit event to database
        setData()
    
    else:
    
        ## log error to database
        log('Error Retrieving event details from sherdog.com: %s' % eventID, xbmc.LOGERROR)


def scanFighter(fighter):

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


def getEvents(promotion = '', fighterID = '', searchStr = '', eventID = ''):

    # get events by promotion
    if not promotion == '':
        return getData("SELECT * FROM events INNER JOIN library ON events.eventID=library.ID WHERE promotion='%s' ORDER BY date" % promotion)
        
    # get events by fighter
    elif not fighterID == '':
        return getData("SELECT events.* FROM events INNER JOIN fights ON events.eventID=fights.eventID WHERE fighterID='%s' ORDER BY date" % fighterID)
    
    # search events
    elif not searchStr == '':
        return getData("SELECT * FROM events INNER JOIN library ON events.eventID=library.ID WHERE (eventID LIKE '%s' OR title LIKE '%s' OR promotion LIKE '%s' OR date LIKE '%s' OR venue LIKE '%s' OR city LIKE '%s') ORDER BY date" % ("%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%"))
    
    # get single event details
    elif not eventID == '':
        return getData("SELECT * FROM events INNER JOIN library ON events.eventID=library.ID WHERE eventID='%s'" % eventID)
    
    # show all events
    else:
        return getData("SELECT * FROM events INNER JOIN library ON events.eventID=library.ID")


def getFighters(searchStr = ''):
    
    # search fighters
    if not searchStr == '':
        return getData("SELECT DISTINCT fighters.*, COUNT(*) AS cnt FROM fighters INNER JOIN fights ON (fights.fighterID=fighters.fighterID) WHERE (fighters.fighterID LIKE '%s' OR fighters.name LIKE '%s' OR fighters.nickname LIKE '%s' OR fighters.association LIKE '%s' OR fighters.city LIKE '%s' OR fighters.country LIKE '%s') GROUP BY fighters.fighterID ORDER BY fighters.name" % ("%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%"))
    
    # show all fighters
    else:
        return getData("SELECT DISTINCT fighters.*, COUNT(*) AS cnt FROM fighters INNER JOIN fights ON (fights.fighterID=fighters.fighterID) GROUP BY fighters.fighterID ORDER BY fighters.name")


def getPromotions():

    # get all promotions
    return getData("SELECT DISTINCT promotion FROM events INNER JOIN library ON events.eventID=library.ID ORDER BY promotion")


def getCounts(promotion = '', fighterID = ''):
    
    # get count of events by promotion
    if not promotion == '':
        return getData("SELECT COUNT(eventID) AS cnt FROM events INNER JOIN library ON events.eventID=library.ID WHERE promotion='%s'" % promotion)
    
    # get count of events by promotion
    elif not fighterID == '':
        return getData("SELECT COUNT(eventID) AS cnt FROM fights WHERE fighterID='%s'" % fighterID)

