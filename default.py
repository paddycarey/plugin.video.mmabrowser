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

## create directories needed for script operation
for neededDir in [__addondir__, __thumbDir__, __fighterDir__, __fightDir__, __promotionDir__]:
        xbmcvfs.mkdir(neededDir)

import resources.lib.databaseops as dbops
import resources.lib.library as library
from resources.lib.utils import *

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

def allEvents():
    for event in dbops.getAllEvents():
        for x in libraryList:
            if event[0] == x['ID']:
                fightList = dbops.getFightersByEvent(event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList)

def browseByOrganisation():
    log('Browsing: Organisations')
    for promotion in dbops.getAllPromotions():
        addPromotion(promotion[0])

def getEventsByOrganisation(organisation):
    log('Listing all events for: %s' % organisation)
    for event in dbops.getEventsByPromotion(organisation):
        for x in libraryList:
            if event[0] == x['ID']:
                fightList = dbops.getFightersByEvent(event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList)

def browseByFighter():
    for fighter in dbops.getAllFighters():
        addFighter(fighter[0], fighter[1], fighter[2], fighter[3], fighter[4], fighter[5], fighter[6], fighter[7], fighter[8], fighter[9], fighter[10])

def getEventsByFighter(fighterID):
    for event in dbops.getEventsByFighter(fighterID):
        for x in libraryList:
            if event[0] == x['ID']:
                fightList = dbops.getFightersByEvent(event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList)

def searchAll():
    searchStr = getUserInput(title = "Search MMA Library")
    for event in dbops.searchEvents(searchStr):
        for x in libraryList:
            if event[0] == x['ID']:
                fightList = getFightersByEvent(event[0])
                addEvent(event[0], event[1], event[2], event[3], event[4], event[5], fightList)
    for fighter in dbops.searchFighters(searchStr):
        addFighter(fighter[0], fighter[1], fighter[2], fighter[3], fighter[4], fighter[5], fighter[6], fighter[7], fighter[8], fighter[9], fighter[10])

def getEvent(eventID):
    event = dbops.getEvent(eventID)
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

    # load library from DB
    libraryList = library.loadLibrary()

    ## check path and generate desired list
    if path == "/":
        library.scanLibrary()
        library.getMissingData()
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

    ## finish adding items to list and display
    xbmcplugin.endOfDirectory(__addonidint__)
