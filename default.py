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
from resources.lib.navigation import *

# workaround for when extrafanart enabled in nox
if sys.argv[0] == 'plugin://plugin.video.mmabrowser/extrafanart/':
    sys.exit(0)

### get addon info
__addon__             = xbmcaddon.Addon()
__addonidint__        = int(sys.argv[1])
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__addonname__         = __addon__.getAddonInfo('name')

#xbmcplugin.setContent(__addonidint__, 'tvshows') 

## parse plugin arguments
params = get_params()

## get path
try:
    path = urllib.unquote_plus(params["path"])
except:
    path = "/"


def updateLibrary():
    import resources.lib.library as library
    library.dialog.create(__addonname__, "MMA Browser", "Loading")
    library.scanLibrary()
    library.getMissingData()
    if __addon__.getSetting("checkMissingExtras") == 'true':
        library.getMissingExtras()
    library.dialog.close()

log('Script path: %s' % path)
log('Library path: %s' % __addon__.getSetting("libraryPath"))

## check path and generate desired list
if path == "/":
    mainMenu()
    ## finish adding items to list and display
    xbmcplugin.endOfDirectory(__addonidint__)
elif path.startswith("/browsebyorganisation"):
    log("path:%s" % path)
    organisation = path.replace('/browsebyorganisation','')
    log("organisation:%s" % organisation)
    if organisation == '':
        ## populate list of organisations
        xbmcplugin.addSortMethod(__addonidint__, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        xbmcplugin.addSortMethod(__addonidint__, xbmcplugin.SORT_METHOD_EPISODE)
        browseByOrganisation()
        ## finish adding items to list and display
        xbmcplugin.endOfDirectory(__addonidint__)
    else:
        ## populate list of events for a given organisation
        xbmcplugin.addSortMethod(__addonidint__, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(__addonidint__, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        getEventsByOrganisation(organisation.lstrip('/'))
        ## finish adding items to list and display
        xbmcplugin.endOfDirectory(__addonidint__)
elif path.startswith("/browsebyfighter"):
    log("path:%s" % path)
    fighterID = path.replace('/browsebyfighter','')
    log("fighterID:%s" % fighterID)
    if fighterID == '':
        ## populate list of fighters
        xbmcplugin.addSortMethod(__addonidint__, xbmcplugin.SORT_METHOD_EPISODE)
        xbmcplugin.addSortMethod(__addonidint__, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(__addonidint__, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        browseByFighter()
        ## finish adding items to list and display
        xbmcplugin.endOfDirectory(__addonidint__)
    else:
        ## populate list of all events a given fighter has fought in
        xbmcplugin.addSortMethod(__addonidint__, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(__addonidint__, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        getEventsByFighter(fighterID.lstrip('/'))
        ## finish adding items to list and display
        xbmcplugin.endOfDirectory(__addonidint__)
elif path == "/allevents":
    ## populate list of all events
    xbmcplugin.addSortMethod(__addonidint__, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(__addonidint__, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    allEvents()
    ## finish adding items to list and display
    xbmcplugin.endOfDirectory(__addonidint__)
elif path == "/search":
    ## populate list of all events
    searchAll()
    ## finish adding items to list and display
    xbmcplugin.endOfDirectory(__addonidint__)
elif path == "/update":
    ## populate list of all events
    updateLibrary()
elif path.startswith("/getEvent/"):
    eventID = path.replace('/getEvent/','')
    ## populate list of all video files for a given event
    getEvent(eventID)
    ## finish adding items to list and display
    xbmcplugin.endOfDirectory(__addonidint__)
