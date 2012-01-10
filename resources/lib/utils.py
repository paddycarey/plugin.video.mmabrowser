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
__artBaseURL__        = "http://mmaartwork.wackwack.co.uk/"



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

def addLink(linkName = '', plot = '', url = '', thumbPath = '', fanartPath = '', plotoutline = '', genre = '', date = '', playable = 'true'):
    if not xbmcvfs.exists(thumbPath):
        thumbPath = "DefaultVideo.png"
    if not xbmcvfs.exists(fanartPath):
        fanartPath = os.path.join(__addonpath__, 'fanart.jpg')
    li = xbmcgui.ListItem(linkName, iconImage = thumbPath, thumbnailImage = thumbPath)
    li.setProperty("IsPlayable", playable)
    li.setInfo( type="Video", infoLabels={ "Title": linkName, "plot": plot, "plotoutline": plotoutline, "genre": genre, "date":date} )
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

def addEvent(eventID = '', eventTitle = '', eventPromotion = '', eventDate = '', eventVenue = '', eventCity = '', fighterList = ''):
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
    fightList = ''
    castList = []
    for fNum, fighter1, fighter2 in fighterList:
        fightList = fightList + "%s vs. %s\n" % (fighter1, fighter2)
        castList.append("%s vs. %s\n" % (fighter1, fighter2))
    description = description + '\n\n' + str(fightList)
    u = sys.argv[0] + "?path=/getEvent/%s" % eventID
    li=xbmcgui.ListItem(label = "[%s] %s" % (eventDate, eventTitle), iconImage = thumbPath, thumbnailImage = thumbPath)
    li.setInfo( type="Video", infoLabels={ "title": eventTitle, "plot": description, "plotoutline": outline, "cast": castList, "genre": eventPromotion, "date": eventDate, "year": int(eventDate.split('-')[0]) } )
    li.setProperty( "Fanart_Image", fanartPath )
    xbmcplugin.addDirectoryItem(handle = __addonidint__, url = u, listitem = li, isFolder = True)

def addFighter(fighterID = '', fighterName = '', fighterNickname = '', fighterAssociation = '', fighterHeight = '', fighterWeight = '', fighterBirthYear = '', fighterBirthMonth = '', fighterBirthDay = '', fighterCity = '', fighterCountry = ''):
    fighterThumb = fighterID + '.jpg'
    thumbPath = os.path.join(__fighterDir__, fighterThumb)
    if not xbmcvfs.exists(thumbPath):
        thumbPath = os.path.join(__addonpath__, 'resources', 'images', 'blank_fighter.jpg')
    fanartPath = os.path.join(__addonpath__, 'fanart.jpg')
    outline = '%s "%s"' % (fighterName, fighterNickname)
    description = "Name: %s\nNickname: %s\nCamp/Association: %s\nHeight: %s\nWeight: %s\nDOB: %s\nCity: %s\nCountry: %s" % (fighterName, fighterNickname, fighterAssociation, fighterHeight, fighterWeight, "%s-%s-%s" % (fighterBirthYear, fighterBirthMonth, fighterBirthDay), fighterCity, fighterCountry)
    log("Adding: Fighter: %s" % fighterName)
    u = sys.argv[0] + "?path=/browsebyfighter/%s" % fighterID
    li=xbmcgui.ListItem(label = fighterName, iconImage = thumbPath, thumbnailImage = thumbPath)
    li.setInfo( type="Video", infoLabels={ "title": fighterName, "plot": description, "plotoutline": outline} )
    li.setProperty( "Fanart_Image", fanartPath )
    xbmcplugin.addDirectoryItem(handle = __addonidint__, url = u, listitem = li, isFolder = True)

def addPromotion(promotionName):
    
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
    li=xbmcgui.ListItem(label = promotionName, iconImage = thumbPath, thumbnailImage = thumbPath)
    li.setInfo( type="Video", infoLabels={ "title": promotionName, "plot": description, "genre": "MMA"} )
    li.setProperty( "Fanart_Image", fanartPath )
    xbmcplugin.addDirectoryItem(handle = __addonidint__, url = u, listitem = li, isFolder = True)

def getMissingExtras():
    if downloadFile(__artBaseURL__ + "repolist.txt", os.path.join(__addondir__, 'repolist.txt')):
        for availableExtra in open(os.path.join(__addondir__, 'repolist.txt')).readlines():
            extraType = availableExtra.split('/', 1)[0]
            extraFilename = availableExtra.split('/', 1)[1].strip()
            if not xbmcvfs.exists(os.path.join(__addondir__, extraType, extraFilename)):
                downloadFile(__artBaseURL__ + availableExtra, os.path.join(__addondir__, extraType, extraFilename))

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

def normalizeString( text ):
    try: text = unicodedata.normalize( 'NFKD', _unicode( text ) ).encode( 'ascii', 'ignore' )
    except: pass
    return text

def log(txt='', severity=xbmc.LOGDEBUG):

    """Log to txt xbmc.log at specified severity"""
    try:
        message = ('MMA Browser: %s' % txt)
        xbmc.log(msg=message, level=severity)
    except UnicodeEncodeError:
        try:
            message = _normalize_string('Artwork Downloader: %s' % txt)
            xbmc.log(msg=message, level=severity)
        except:
            message = ('Artwork Downloader: UnicodeEncodeError')
            xbmc.log(msg=message, level=xbmc.LOGWARNING)

def getHtml(url):
    try:
        client = urlopen(url)
        data = client.read()
        client.close()
    except:
        log('Error getting data from: %s' % url)
    else:
        log('Retrieved URL: %s' % url)
        return data
