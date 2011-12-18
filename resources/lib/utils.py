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
__thumbDir__          = os.path.join(__addondir__, 'thumbs')
__fighterDir__        = os.path.join(__addondir__, 'fighters')
__promotionDir__      = os.path.join(__addondir__, 'promotions')
__artBaseURL__        = "http://dl.dropbox.com/u/266793/mmaartwork/"



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

def addLink(name, descr, url, iconimage, fanart='', fallbackFanart=''):
    if not xbmcvfs.exists(iconimage):
        iconimage=''
    li = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    li.setProperty("IsPlayable", "true")
    li.setInfo( type="Video", infoLabels={ "Title": name , "plot": descr, "plotoutline": descr.replace('\n','')} )
    if xbmcvfs.exists(fanart):
        li.setProperty( "Fanart_Image", fanart )
    elif xbmcvfs.exists(fallbackFanart):
        li.setProperty( "Fanart_Image", fallbackFanart )
    else:
        li.setProperty( "Fanart_Image", os.path.join(__addonpath__, 'fanart.jpg'))
    xbmcplugin.addDirectoryItem(handle=__addonidint__,url=url,listitem=li, isFolder=False)

def addDir(name, path, page, iconimage, fanart='', fallbackFanart=''):
    if not xbmcvfs.exists(iconimage):
        iconimage=''
    u=sys.argv[0]+"?path=%s&page=%s"%(path,str(page))
    li=xbmcgui.ListItem(name, iconImage="DefaultFolder.png",thumbnailImage=iconimage)
    li.setInfo( type="Video", infoLabels={ "Title": name })
    #li.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "Date": date } )
    if xbmcvfs.exists(fanart):
        li.setProperty( "Fanart_Image", fanart )
    elif xbmcvfs.exists(fallbackFanart):
        li.setProperty( "Fanart_Image", fallbackFanart )
    else:
        li.setProperty( "Fanart_Image", os.path.join(__addonpath__, 'fanart.jpg'))
    xbmcplugin.addDirectoryItem(handle=__addonidint__,url=u,listitem=li,isFolder=True)

# This function raises a keyboard for user input
def getUserInput(self, title = "Input", default="", hidden=False):
    result = None

    # Fix for when this functions is called with default=None
    if not default:
        default = ""

    keyboard = self.xbmc.Keyboard(default, title)
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
        xbmcvfs.delete(filePath)
        log('Unable to download: %s' % url)
    else:
        log("Downloaded: %s" % url)

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
        
def getArtwork(promotionName=None, eventID=None):
    eventThumb = eventID + '-poster.jpg'
    eventThumbPath = os.path.join(__thumbDir__, eventThumb)
    if not xbmcvfs.exists(eventThumbPath):
        thumbUrl = __artBaseURL__ + 'events/' + eventThumb
        downloadFile(thumbUrl, eventThumbPath)

    eventFanart = eventID + '-fanart.jpg'
    eventFanartPath = os.path.join(__thumbDir__, eventFanart)
    if not xbmcvfs.exists(eventFanartPath):
        fanartUrl = __artBaseURL__ + 'events/' + eventFanart
        downloadFile(fanartUrl, eventFanartPath)

    promotionThumb = promotionName + '-poster.jpg'
    promotionThumbPath = os.path.join(__promotionDir__, promotionThumb)
    if not xbmcvfs.exists(promotionThumbPath):
        fanartUrl = __artBaseURL__ + 'promotions/' + promotionThumb
        downloadFile(fanartUrl, promotionThumbPath)

    promotionFanart = promotionName + '-fanart.jpg'
    promotionFanartPath = os.path.join(__promotionDir__, promotionFanart)
    if not xbmcvfs.exists(promotionFanartPath):
        fanartUrl = __artBaseURL__ + 'promotions/' + promotionFanart
        downloadFile(fanartUrl, promotionFanartPath)
