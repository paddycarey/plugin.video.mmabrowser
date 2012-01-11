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
__addonidint__        = int(sys.argv[1])
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('profile'))


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
        xbmcplugin.addSortMethod(__addonidint__, 3)
        xbmcplugin.addSortMethod(__addonidint__, 23)
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
    xbmcplugin.addSortMethod(__addonidint__, 3)
    xbmcplugin.addSortMethod(__addonidint__, 23)
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
