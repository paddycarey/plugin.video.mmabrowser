#!/usr/bin/env python

import os
import xbmc
import xbmcaddon
import xbmcvfs

from resources.lib.utils import *
import resources.lib.databaseops as dbops
import resources.lib.library as library

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

### get addon info
__addon__             = xbmcaddon.Addon()
__addonpath__         = __addon__.getAddonInfo('path')
__addonid__         = __addon__.getAddonInfo('id')
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__thumbDir__          = os.path.join(__addondir__, 'events')
__promotionDir__      = os.path.join(__addondir__, 'promotions')

# initialise cache object to speed up plugin operation
cache = StorageServer.StorageServer(__addonid__ + '-fightlists', 24*7)

def mainMenu():
    log('Showing main menu')
    addDir("Browse by: Organisation", "/browsebyorganisation/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Browse a list of all MMA Promotions in your library.")
    addDir("Browse by: Fighter", "/browsebyfighter/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Browse a list of all fighters in your library")
    addDir("All Events", "/allevents/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Browse a list of all events in your library")
    addDir("Search", "/search/", os.path.join(__addonpath__, "resources", "images", "generic_poster.jpg"), "", "Search all items in your library")

def allEvents():
    log('Browsing: All events')
    dbList = dbops.getAllEvents()
    totalEvents = len(dbList)
    for event in dbList:
        for x in library.loadLibrary():
            if event[0] == x['ID']:
                fightList = cache.cacheFunction(dbops.getFightersByEvent, event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList, totalEvents)

def browseByOrganisation():
    log('Browsing: Organisations')
    for promotion in dbops.getAllPromotions():
        addPromotion(promotion[0], dbops.getEventCount(promotion[0]))

def getEventsByOrganisation(organisation):
    log('Listing all events for: %s' % organisation)
    dbList = dbops.getEventsByPromotion(organisation)
    totalEvents = len(dbList)
    for event in dbList:
        for x in library.loadLibrary():
            if event[0] == x['ID']:
                fightList = cache.cacheFunction(dbops.getFightersByEvent, event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList, totalEvents)

def browseByFighter():
    log('Browsing: Fighters')
    dbList = dbops.getAllFighters()
    totalFighters = len(dbList)
    for fighter in dbList:
        addFighter(fighter[0], fighter[1], fighter[2], fighter[3], fighter[4], fighter[5], fighter[6], fighter[7], fighter[8], fighter[10], totalFighters, fighter[9])

def getEventsByFighter(fighterID):
    log('Listing all events for: %s' % fighterID)
    dbList = dbops.getEventsByFighter(fighterID)
    totalEvents = len(dbList)
    for event in dbList:
        for x in library.loadLibrary():
            if event[0] == x['ID']:
                fightList = cache.cacheFunction(dbops.getFightersByEvent, event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList, totalEvents)

def searchAll():
    log('Searching MMA Library')
    searchStr = getUserInput(title = "Search MMA Library")
    if searchStr:
        dbList = dbops.searchEvents(searchStr)
        totalEvents = len(dbList)
        dbList2 = dbops.searchFighters(searchStr)
        totalFighters = len(dbList2)
        totalListItems = totalEvents + totalFighters
        for event in dbList:
            for x in library.loadLibrary():
                if event[0] == x['ID']:
                    fightList = cache.cacheFunction(dbops.getFightersByEvent, event[0])
                    addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList, totalListItems)
        for fighter in dbList2:
            addFighter(fighter[0], fighter[1], fighter[2], fighter[3], fighter[4], fighter[5], fighter[6], fighter[7], fighter[8], fighter[10], totalListItems, fighter[9])

def getEvent(eventID):
    event = dbops.getEvent(eventID)
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
            fighterList = cache.cacheFunction(dbops.getFightersByEvent, eventID)
            description = description + '\n\n' + '\n'.join(fighterList)
            fileList = getVideoList(x['path'])
            if len(fileList) == 1:
                li=xbmcgui.ListItem(label = event[1], iconImage = thumbPath, thumbnailImage = thumbPath)
                li.setInfo( type="Video", infoLabels={ "title": event[1], "plot": description, "cast": fighterList, "genre": event[2], "date": event[3], "premiered": event[3], "tvshowtitle": event[2]} )
                xbmc.Player().play(fileList[0]['path'], li)
                sys.exit(0)
            else:
                for vidFile in fileList:
                    addLink(linkName = vidFile['title'], plotoutline = outline, plot = description, url = vidFile['path'], thumbPath = thumbPath, fanartPath = fanartPath, genre = event[2])

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
    
