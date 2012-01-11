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

import resources.lib.library as library
from resources.lib.utils import *
from resources.lib.navigation import *

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

## create directories needed for script operation
for neededDir in [__addondir__, __thumbDir__, __fighterDir__, __fightDir__, __promotionDir__]:
        xbmcvfs.mkdir(neededDir)

xbmcplugin.setContent(__addonidint__, 'tvshows') 

## parse plugin arguments
params = get_params()

## get path
try:
    path = urllib.unquote_plus(params["path"])
except:
    path = "/"

log('Script path: %s' % path)

## check path and generate desired list
if path == "/":
    library.scanLibrary()
    library.getMissingData()
    if __addon__.getSetting("checkMissingExtras") == 'true':
        getMissingExtras()
    mainMenu()
elif path.startswith("/browsebyorganisation"):
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
