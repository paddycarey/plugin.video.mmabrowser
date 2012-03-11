#!/usr/bin/env python

import os
import xbmc
import xbmcaddon
import xbmcvfs

from resources.lib.utils import *
import resources.lib.library as library


### get addon info
__addon__             = xbmcaddon.Addon()
__addonpath__         = __addon__.getAddonInfo('path')
__addonid__         = __addon__.getAddonInfo('id')
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__thumbDir__          = os.path.join(__addondir__, 'events')
__promotionDir__      = os.path.join(__addondir__, 'promotions')


def mainMenu():
    log('Showing main menu')
    addDir("Browse by: Organisation", "/browsebyorganisation/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Browse a list of all MMA Promotions in your library.")
    addDir("Browse by: Fighter", "/browsebyfighter/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Browse a list of all fighters in your library")
    addDir("All Events", "/allevents/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Browse a list of all events in your library")
    addDir("Search", "/search/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Search all items in your library")
    addDir("Update Library", "/update/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Scan your library for new events")


def allEvents():
    log('Browsing: All events')
    dbList = library.getEvents()
    totalEvents = len(dbList)
    libraryList = library.loadLibrary()
    for event in dbList:
        for x in libraryList:
            if event[0] == x['ID']:
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], event[6], totalEvents)
                break


def browseByOrganisation():
    log('Browsing: Organisations')
    for promotion in library.getPromotions():
        eventCount = library.getCounts(promotion = promotion['promotion'])[0]['cnt']
        addPromotion(promotion['promotion'], eventCount)


def getEventsByOrganisation(organisation):
    log('Listing all events for: %s' % organisation)
    dbList = library.getEvents(promotion = organisation)
    totalEvents = len(dbList)
    libraryList = library.loadLibrary()
    for event in dbList:
        for x in libraryList:
            if event['eventID'] == x['ID']:
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], event[6], totalEvents)
                break


def browseByFighter():
    log('Browsing: Fighters')
    dbList = library.getFighters()
    totalFighters = len(dbList)
    for fighter in dbList:
        addFighter(fighter[0], fighter[1], fighter[2], fighter[3], fighter[4], fighter[5], fighter[6], fighter[7], fighter[8], fighter[10], totalFighters, fighter[9])


def getEventsByFighter(fighterID):
    log('Listing all events for: %s' % fighterID)
    dbList = library.getEvents(fighterID = fighterID)
    totalEvents = len(dbList)
    libraryList = library.loadLibrary()
    for event in dbList:
        for x in libraryList:
            if event[0] == x['ID']:
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], event[6], totalEvents)
                break


def searchAll():
    log('Searching MMA Library')
    searchStr = getUserInput(title = "Search MMA Library")
    if searchStr:
        dbList = library.getEvents(searchStr = searchStr)
        totalEvents = len(dbList)
        dbList2 = library.getFighters(searchStr = searchStr)
        totalFighters = len(dbList2)
        totalListItems = totalEvents + totalFighters
        libraryList = library.loadLibrary()
        for event in dbList:
            for x in libraryList:
                if event[0] == x['ID']:
                    addEvent(event[0], event[1], event[2], event[3], event[4], event[5], event[6], totalListItems)
                    break
        for fighter in dbList2:
            addFighter(fighter[0], fighter[1], fighter[2], fighter[3], fighter[4], fighter[5], fighter[6], fighter[7], fighter[8], fighter[10], totalListItems, fighter[9])


def getEvent(eventID):
    event = library.getEvents(eventID = eventID)[0]
    log('Listing video files for event: %s' % event[1])
    for x in library.loadLibrary():
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
            description = description + '\n\n' + event[6]
            fileList = getVideoList(x['path'])
            for vidFile in fileList:
                addLink(linkName = vidFile['title'], plotoutline = outline, plot = description, url = vidFile['path'], thumbPath = thumbPath, fanartPath = fanartPath, genre = event[1], tvshowtitle = event[1])


def getVideoList(rootDir):
    stackCounter = 1
    activeStack = ''
    fileList = []
    for filename in library.getFileList(rootDir):
        stackPart = 'cd' + str(stackCounter)
        if stackPart in filename:
                if stackCounter == 1:
                    if not activeStack == '':
                        if not activeStack in fileList:
                            fileList.append(activeStack)
                    activeStack = 'stack://' + filename
                    stackCounter = 2
                else:
                    activeStack = activeStack + ' , ' + filename
                    stackCounter = stackCounter + 1
        else:
            if not activeStack == '':
                if not activeStack in fileList:
                    fileList.append(activeStack)
                    stackCounter = 1
                    activeStack = ''
            else:
                if not filename in fileList:
                    fileList.append(filename)
    if not activeStack == '':
        if not activeStack in fileList:
            fileList.append(activeStack)
    vidFiles = []
    for vidFileName in sorted(fileList):
        vidFile = {}
        vidFile['path'] = vidFileName
        if __addon__.getSetting("cleanFilenames") == 'true':
            vidFile['title'] = os.path.splitext(os.path.split(vidFileName)[1])[0].lstrip('0123456789. ')
            if '.cd' in vidFile['title']:
                vidFile['title'] = os.path.splitext(vidFile['title'])[0]
        else:
            vidFile['title'] = os.path.split(vidFileName)[1]
        if os.path.splitext(vidFileName)[1].lower() in xbmc.getSupportedMedia('video').split('|') and not '-sample' in vidFileName.lower():
            vidFiles.append(vidFile)
        else:
            log('File ignored: %s' % vidFile['path'])
    return vidFiles
    
