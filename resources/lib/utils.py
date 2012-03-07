#!/usr/bin/env python

import os
import socket
import sys

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from urllib2 import urlopen

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
__fightDir__        = os.path.join(__addondir__, 'fights')
__promotionDir__      = os.path.join(__addondir__, 'promotions')

## create directories needed for script operation
for neededDir in [__addondir__, __thumbDir__, __fighterDir__, __fightDir__, __promotionDir__]:
        xbmcvfs.mkdir(neededDir)

### adjust default timeout to stop script hanging
timeout = 20
socket.setdefaulttimeout(timeout)

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

def getUniq(seq): 
    seen = []
    result = []
    for item in seq:
        if item in seen: continue
        seen.append(item)
        result.append(item)
    return result

def addLink(linkName = '', plot = '', url = '', thumbPath = '', fanartPath = '', plotoutline = '', genre = '', date = '', playable = 'true', tvshowtitle = ''):
    if not xbmcvfs.exists(thumbPath):
        thumbPath = "DefaultVideo.png"
    if not xbmcvfs.exists(fanartPath):
        fanartPath = os.path.join(__addonpath__, 'fanart.jpg')
    li = xbmcgui.ListItem(linkName, iconImage = thumbPath, thumbnailImage = thumbPath)
    li.setProperty("IsPlayable", playable)
    li.setInfo( type="Video", infoLabels={ "Title": linkName, "TVShowTitle": tvshowtitle, "plot": plot, "genre": genre, "date":date} )
    li.setProperty( "Fanart_Image", fanartPath)
    xbmcplugin.addDirectoryItem(handle = __addonidint__, url = url, listitem = li, isFolder = False)

def addDir(dirName, targetPath, thumbPath, fanartPath, description):
    if not xbmcvfs.exists(thumbPath):
        thumbPath = "DefaultFolder.png"
    if not xbmcvfs.exists(fanartPath):
        fanartPath = os.path.join(__addonpath__, 'fanart.jpg')
    u = sys.argv[0] + "?path=%s" % targetPath
    li = xbmcgui.ListItem(dirName, iconImage = thumbPath, thumbnailImage = thumbPath)
    li.setInfo( type="Video", infoLabels={ "Title": dirName , "Plot": description})
    li.setProperty( "Fanart_Image", fanartPath)
    xbmcplugin.addDirectoryItem(handle = __addonidint__ , url = u, listitem = li, isFolder = True)

def addEvent(eventID = '', eventTitle = '', eventPromotion = '', eventDate = '', eventVenue = '', eventCity = '', fighterList = '', totalEvents = 0):
    thumbPath = os.path.join(__thumbDir__, '%s-poster.jpg' % eventID)
    if not xbmcvfs.exists(thumbPath):
        thumbPath = os.path.join(__promotionDir__, '%s-poster.jpg' % eventPromotion.replace(' ', ''))
        if not xbmcvfs.exists(thumbPath):
            thumbPath = "DefaultFolder.png"
    fanartPath = os.path.join(__thumbDir__, '%s-fanart.jpg' % eventID)
    if not xbmcvfs.exists(fanartPath):
        fanartPath = os.path.join(__promotionDir__, '%s-fanart.jpg' % eventPromotion.replace(' ', ''))
        if not xbmcvfs.exists(fanartPath):
            fanartPath = os.path.join(__addonpath__, 'fanart.jpg')
    outline = '%s: %s, %s' % (eventDate, eventVenue, eventCity)
    try:
        description = open(os.path.join(__thumbDir__, '%s-description.txt' % eventID)).read()
    except IOError:
        description = outline
    log("Adding: Event: %s: %s" % (eventDate, eventTitle))
    description = description + '\n\n' + '\n'.join(fighterList)
    u = sys.argv[0] + "?path=/getEvent/%s" % eventID
    li=xbmcgui.ListItem(label = "[%s] %s" % (eventDate, eventTitle), iconImage = thumbPath, thumbnailImage = thumbPath)
    li.setInfo( type="Video", infoLabels={ "title": eventTitle, "plot": description, "plotoutline": outline, "cast": fighterList, "genre": eventPromotion, "date": eventDate, "year": int(eventDate.split('-')[0]), "premiered": eventDate, "tvshowtitle": eventTitle} )
    li.setProperty( "Fanart_Image", fanartPath )
    xbmcplugin.addDirectoryItem(handle = __addonidint__, url = u, listitem = li, isFolder = True, totalItems = int(totalEvents))

def addFighter(fighterID = '', fighterName = '', fighterNickname = '', fighterAssociation = '', fighterHeight = '', fighterWeight = '', fighterBirthDate = '', fighterCity = '', fighterCountry = '', fightCount = '', totalFighters = '', thumbURL = ''):
    fanartPath = os.path.join(__addonpath__, 'fanart.jpg')
    description = "Name: %s\nNickname: %s\nCamp/Association: %s\nHeight: %s\nWeight: %s\nDOB: %s\nCity: %s\nCountry: %s" % (fighterName, fighterNickname, fighterAssociation, fighterHeight, fighterWeight, fighterBirthDate, fighterCity, fighterCountry)
    log("Adding: Fighter: %s" % fighterName)
    u = sys.argv[0] + "?path=/browsebyfighter/%s" % fighterID
    li=xbmcgui.ListItem(label = '%s (%s)' % (fighterName, fightCount), iconImage = thumbURL, thumbnailImage = thumbURL)
    li.setInfo( type="Video", infoLabels={ "title": fighterName, "plot": description, "tvshowtitle": fighterName, "episode": fightCount, "aired": fighterBirthDate} )
    li.setProperty( "Fanart_Image", fanartPath )
    li.setProperty( "TotalEpisodes", str(fightCount) )
    li.setProperty( "TotalSeasons", '1' )
    xbmcplugin.addDirectoryItem(handle = __addonidint__, url = u, listitem = li, isFolder = True, totalItems = int(totalFighters))

def addPromotion(promotionName, eventCount):
    
    if __addon__.getSetting("useBanners") == 'true':
        promotionThumb = promotionName + '-banner.jpg'
    else:
        promotionThumb = promotionName + '-poster.jpg'
    thumbPath = os.path.join(__promotionDir__, promotionThumb.replace(' ', ''))
    if not xbmcvfs.exists(thumbPath):
        thumbPath = "DefaultFolder.png"

    promotionFanart = promotionName + '-fanart.jpg'
    fanartPath = os.path.join(__promotionDir__, promotionFanart.replace(' ', ''))
    if not xbmcvfs.exists(fanartPath):
        fanartPath = os.path.join(__addonpath__, 'fanart.jpg')

    try:
        description = open(os.path.join(__promotionDir__, '%s-description.txt' % promotionName.replace(' ', ''))).read()
    except IOError:
        description = ''

    log("Adding: Promotion: %s" % promotionName)
    u = sys.argv[0] + "?path=/browsebyorganisation/%s" % promotionName
    li=xbmcgui.ListItem(label = "%s (%s)" % (promotionName, eventCount), iconImage = thumbPath, thumbnailImage = thumbPath)
    li.setInfo( type="Video", infoLabels={ "Title": promotionName, "Plot": description, "Genre": "MMA", "TVShowTitle": promotionName, "episode": eventCount} )
    li.setProperty( "Fanart_Image", fanartPath )
    li.setProperty( "TotalEpisodes", str(eventCount) )
    li.setProperty( "TotalSeasons", '1' )
    xbmcplugin.addDirectoryItem(handle = __addonidint__, url = u, listitem = li, isFolder = True)

# This function raises a keyboard for user input
def getUserInput(title = "Input", default="", hidden=False):
    result = None

    # Fix for when this functions is called with default=None
    if not default:
        default = ""

    keyboard = xbmc.Keyboard(default, title)
    keyboard.setHiddenInput(hidden)
    keyboard.doModal()

    if keyboard.isConfirmed():
        result = keyboard.getText()

    return result

def downloadFile(url, filePath):

    """
    Download url to filePath.
    """
    try:
        dlFile = open(filePath, "wb")
        response = urlopen(url)
        dlFile.write(response.read())
        dlFile.close()
        response.close()
    except:
        if xbmcvfs.exists(filePath):
            xbmcvfs.delete(filePath)
            log('Unable to download: %s' % url)
            return False
    else:
        log("Downloaded: %s" % url)
        return True


def log(txt='', severity=xbmc.LOGDEBUG):

    """Log to txt xbmc.log at specified severity"""
    message = ('MMA Browser: %s' % txt.encode('utf-8'))
    xbmc.log(msg=message, level=severity)

