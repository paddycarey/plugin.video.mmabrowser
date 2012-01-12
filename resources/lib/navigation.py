#!/usr/bin/env python

import os
import xbmc
import xbmcaddon
import xbmcvfs

from resources.lib.utils import *
import resources.lib.databaseops as dbops
import resources.lib.library as library

### get addon info
__addon__             = xbmcaddon.Addon()
__addonpath__         = __addon__.getAddonInfo('path')
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__thumbDir__          = os.path.join(__addondir__, 'events')
__promotionDir__      = os.path.join(__addondir__, 'promotions')


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
                fightList = dbops.getFightersByEvent(event[0])
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
                fightList = dbops.getFightersByEvent(event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList, totalEvents)

def browseByFighter():
    log('Browsing: Fighters')
    dbList = dbops.getAllFighters()
    totalFighters = len(dbList)
    for fighter in dbList:
        addFighter(fighter[0], fighter[1], fighter[2], fighter[3], fighter[4], fighter[5], fighter[6], fighter[7], fighter[8], fighter[9], fighter[10], fighter[11], totalFighters)

def getEventsByFighter(fighterID):
    log('Listing all events for: %s' % fighterID)
    dbList = dbops.getEventsByFighter(fighterID)
    totalEvents = len(dbList)
    for event in dbList:
        for x in library.loadLibrary():
            if event[0] == x['ID']:
                fightList = dbops.getFightersByEvent(event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList, totalEvents)

def searchAll():
    log('Searching MMA Library')
    searchStr = getUserInput(title = "Search MMA Library")
    dbList = dbops.searchEvents(searchStr)
    totalEvents = len(dbList)
    dbList2 = dbops.searchFighters(searchStr)
    totalFighters = len(dbList2)
    totalListItems = totalEvents + totalFighters
    for event in dbList:
        for x in library.loadLibrary():
            if event[0] == x['ID']:
                fightList = dbops.getFightersByEvent(event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList, totalListItems)
    for fighter in dbList2:
        addFighter(fighter[0], fighter[1], fighter[2], fighter[3], fighter[4], fighter[5], fighter[6], fighter[7], fighter[8], fighter[9], fighter[10], fighter[11], totalListItems)

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
            fighterList = dbops.getFightersByEvent(eventID)
            description = description + '\n\n' + '\n'.join(fighterList)
            fileList = getFileList(x['path'])
            if len(fileList) == 1:
                li=xbmcgui.ListItem(label = "[%s] %s" % (event[3], event[1]), iconImage = thumbPath, thumbnailImage = thumbPath)
                li.setInfo( type="Video", infoLabels={ "title": event[1], "plot": description, "cast": fighterList, "genre": 'MMA', "date": event[3], "premiered": event[3], "tvshowtitle": event[2]} )
                xbmc.Player().play(fileList[0]['path'], li)
                sys.exit(0)
            else:
                for vidFile in fileList:
                    addLink(linkName = vidFile['title'], plotoutline = outline, plot = description, url = vidFile['path'], thumbPath = thumbPath, fanartPath = fanartPath, genre = 'MMA')

def getFileList(rootDir):

    stackCounter = 1
    activeStack = ''
    fileList = []
    for root, dirs, files in os.walk(rootDir):
            for filename in sorted(files):
                stackPart = 'cd' + str(stackCounter)
                if stackPart in filename:
                        if stackCounter == 1:
                            activeStack = 'stack://' + os.path.join(root, filename)
                            stackCounter = 2
                        else:
                            activeStack = activeStack + ' , ' + os.path.join(root, filename)
                            stackCounter = stackCounter + 1
                else:
                    if not activeStack == '':
                        if not activeStack in fileList:
                            fileList.append(activeStack)
                            stackCounter = 1
                            activeStack = ''
                    else:
                        if not os.path.join(root, filename) in fileList:
                            fileList.append(os.path.join(root, filename))
    vidFiles = []
    for vidFileName in sorted(fileList):
        vidFile = {}
        vidFile['path'] = vidFileName
        if __addon__.getSetting("cleanFilenames") == 'true':
            vidFile['title'] = os.path.splitext(os.path.splitext(os.path.split(vidFileName)[1])[0])[0].lstrip('0123456789. ')
        else:
            vidFile['title'] = os.path.split(vidFileName)[1]
        if os.path.splitext(vidFileName)[1] in xbmc.getSupportedMedia('video').split('|'):
            vidFiles.append(vidFile)
        else:
            log('File ignored: %s' % vidFile['path'])
    return vidFiles
    
