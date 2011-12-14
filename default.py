#!/usr/bin/env python

# Some links used for testing
# Andre Gusmao http://www.sherdog.com/fightfinder/fightfinder.asp?fighterID=15806
# UFC 98 http://www.sherdog.com/fightfinder/fightfinder.asp?eventID=9529

import os
import shelve
import socket
import sys
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup

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
__eventDir__          = os.path.join(__addondir__, 'events')

### adjust default timeout to stop script hanging
timeout = 20
socket.setdefaulttimeout(timeout)

page = 1
path = "/"

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
        log( 'Error getting data from: %s' % url )
    else:
        return data

def scanLibrary(path):
    library = []
    idFile = 'sherdogEventID'
    for x in os.walk(path):
        pathIdFile = os.path.join(x[0], idFile)
        if xbmcvfs.exists(pathIdFile):
            event = {}
            event['ID'] = open(pathIdFile).read()
            event['path'] = x[0]
            library.append(event)
    return library

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
    else:
        log("Downloaded: %s" % url, xbmc.LOGNOTICE)

class getEventDetails:
    
    def __init__(self, sherdogEventID):
        
        shelveFilePath = os.path.join(__eventDir__, sherdogEventID)
        shelveFile = shelve.open(shelveFilePath)
        self.ID = sherdogEventID
        try:
            self.title = shelveFile['title']
            self.promotion = shelveFile['promotion']
            self.date = shelveFile['date']
            self.venue = shelveFile['venue']
            self.city = shelveFile['city']
            self.fights = shelveFile['fights']
        except:
            url = 'http://www.sherdog.com/fightfinder/fightfinder.asp?eventID=%s' % sherdogEventID
            soup = BeautifulSoup(getHtml(url))
            self.title = soup.find("div", {"class" : "Txt30Blue Bold SpacerLeft8"}).h1.string
            self.promotion = soup.find("div", {"class" : "Txt13Orange Bold SpacerLeft8"}).a.string
            self.date = soup.find("div", {"class" : "Txt13White Bold SpacerLeft8"}).string
            self.venue = soup.find("div", {"class" : "Txt13Gray Bold SpacerLeftBottom8"}).findAll(text=True)[0].rstrip(',')
            try:
                self.city = soup.find("div", {"class" : "Txt13Gray Bold SpacerLeftBottom8"}).findAll(text=True)[1].rstrip('\r\n')
            except:
                self.city = ''
            table = soup.find("table", {"class" : "fight_event_card"})
            rows = table.findAll('tr')
            self.fights = []
            rowcount = 0
            for row in rows:
                if not rowcount == 0:
                    cols = row.findAll('td')
                    
                    fight = {}
                    fight['ID'] = cols[0].string
                    fight['fighters'] = []
                    fight['fighters'].append(cols[1].a['href'].rsplit('-', 1)[1])
                    fight['fighters'].append(cols[3].a['href'].rsplit('-', 1)[1])
                    if cols[1].findAll(text=True)[1] == 'Winner':
                        fight['winner'] = cols[1].a['href'].rsplit('-', 1)[1]
                    else:
                        fight['winner'] = None
                    fight['result'] = cols[4].string
                    fight['round'] = cols[5].string
                    fight['time'] = cols[6].string
                    self.fights.append(fight)
                    
                rowcount = rowcount + 1
                
            shelveFile['title'] = self.title
            shelveFile['promotion'] = self.promotion
            shelveFile['date'] = self.date
            shelveFile['venue'] = self.venue
            shelveFile['city'] = self.city
            shelveFile['fights'] = self.fights
        shelveFile.close()

class getFighterDetails:
    
    def __init__(self, sherdogFighterID):

        url = 'http://www.sherdog.com/fightfinder/fightfinder.asp?fighterID=%s' % sherdogFighterID
        shelveFilePath = os.path.join(__fighterDir__, sherdogFighterID)
        shelveFile = shelve.open(shelveFilePath)

        self.ID = sherdogFighterID
        self.name = None
        self.nickName = None
        self.association = None
        self.height = None
        self.weight = None
        self.birthYear = None
        self.birthMonth = None
        self.birthDay = None
        self.age = None
        self.city = None
        self.country = None

        try:
            self.name = shelveFile['name']
            self.nickName = shelveFile['nickName']
            self.association = shelveFile['association']
            self.height = shelveFile['height']
            self.weight = shelveFile['weight']
            self.birthYear = shelveFile['birthYear']
            self.birthMonth = shelveFile['birthMonth']
            self.birthDay = shelveFile['birthDay']
            self.age = shelveFile['age']
            self.city = shelveFile['city']
            self.country = shelveFile['country']
            fighterThumb = self.ID + '.jpg'
            thumbPath = os.path.join(__fighterDir__, fighterThumb)
            if not xbmcvfs.exists(thumbPath):
                soup = BeautifulSoup(getHtml(url))
                thumbUrl = soup.find("span", {"id" : "fighter_picture"}).img['src']
                if not thumbUrl == 'http://www.cdn.sherdog.com/fightfinder/Pictures/blank_fighter.jpg':
                    downloadFile(thumbUrl, thumbPath)
        except:
            soup = BeautifulSoup(getHtml(url))
    
            table = soup.find("span", {"id" : "fighter_profile"})
            rows = table.findAll('tr')
            for row in rows:
                infoItem = row.findAll('td')
                if infoItem[0].string == None:
                    continue
                if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Name':
                    self.name = infoItem[1].string.rstrip(' ').rstrip('\n')
                if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Nick Name':
                    self.nickName = infoItem[1].string.rstrip(' ').rstrip('\n')
                if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Association':
                    self.association = infoItem[1].a.string.rstrip(' ').rstrip('\n')
                if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Height':
                    self.height = infoItem[1].string.rstrip(' ').rstrip('\n')
                if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Weight':
                    self.weight = infoItem[1].string.rstrip(' ').rstrip('\n')
                if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Birth Date':
                    self.birthYear = infoItem[1].string.rstrip(' ').rstrip('\n').split('-')[0]
                    self.birthMonth = infoItem[1].string.rstrip(' ').rstrip('\n').split('-')[1]
                    self.birthDay = infoItem[1].string.rstrip(' ').rstrip('\n').split('-')[2]
                if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Age':
                    self.age = infoItem[1].string.rstrip(' ').rstrip('\n')
                if infoItem[0].string.rstrip(' ').rstrip('\n') == 'City':
                    self.city = infoItem[1].string.rstrip(' ').rstrip('\n')
                if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Country':
                    self.country = infoItem[1].string.rstrip(' ').rstrip('\n')
            
            shelveFile['name'] = self.name
            shelveFile['nickName'] = self.nickName
            shelveFile['association'] = self.association
            shelveFile['height'] = self.height
            shelveFile['weight'] = self.weight
            shelveFile['birthYear'] = self.birthYear
            shelveFile['birthMonth'] = self.birthMonth
            shelveFile['birthDay'] = self.birthDay
            shelveFile['age'] = self.age
            shelveFile['city'] = self.city
            shelveFile['country'] = self.country
        
            fighterThumb = self.ID + '.jpg'
            thumbPath = os.path.join(__fighterDir__, fighterThumb)
            if not xbmcvfs.exists(thumbPath):
                thumbUrl = soup.find("span", {"id" : "fighter_picture"}).img['src']
                if not thumbUrl == 'http://www.cdn.sherdog.com/fightfinder/Pictures/blank_fighter.jpg':
                    downloadFile(thumbUrl, thumbPath)
                    
        shelveFile.close()

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

def addLink(name,descr, url,iconimage):
    if not xbmcvfs.exists(iconimage):
        iconimage=''
    li = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    li.setProperty("IsPlayable", "true")
    li.setInfo( type="Video", infoLabels={ "Title": name , "plot": descr, "plotoutline": descr} )
    xbmcplugin.addDirectoryItem(handle=__addonidint__,url=url,listitem=li, isFolder=False)

def addDir(name,path,page,iconimage):
    if not xbmcvfs.exists(iconimage):
        iconimage=''
    u=sys.argv[0]+"?path=%s&page=%s"%(path,str(page))
    li=xbmcgui.ListItem(name, iconImage="DefaultFolder.png",thumbnailImage=iconimage)
    li.setInfo( type="Video", infoLabels={ "Title": name })
    xbmcplugin.addDirectoryItem(handle=__addonidint__,url=u,listitem=li,isFolder=True)

def doTestRun():
    # Simple test run
    
    library = [{ 'ID' : '9529', 'path' : '/media/raid5/mma_sorted/[2009-05-23] UFC 98: Evans vs. Machida'},{ 'ID' : '17789', 'path' : '/media/raid5/mma_sorted/[2009-05-23] UFC Live: Cruz vs. Johnson'},{ 'ID' : '16309', 'path' : '/media/raid5/mma_sorted/[2011-06-26] UFC Live: Kongo vs. Barry'},{ 'ID' : '8732', 'path' : '/media/raid5/mma_sorted/[2008-12-27] UFC 92: The Ultimate 2008'}]
    
    card = getEventDetails('9529')
    
    log( '##### Event Details #####' )
    log( 'Name:      %s' % card.title )
    log( 'Promotion: %s' % card.promotion )
    log( 'Date:      %s' % card.date )
    log( 'Venue:     %s' % card.venue )
    log( 'City:      %s' % card.city )
    for fight in card.fights:
        for fighter in fight['fighters']:
            details = getFighterDetails(fighter)
            log()
            log( '##### Fighter Details #####' )
            log( 'Name:          %s' % details.name )
            log( 'Nickname:      %s' % details.nickName )
            log( 'Camp:          %s' % details.association )
            log( 'Height:        %s' % details.height )
            log( 'Weight:        %s' % details.weight )
            log( 'Date of birth: %s-%s-%s' % (details.birthYear, details.birthMonth, details.birthDay) )
            log( 'Age:           %s' % details.age )
            log( 'City:          %s' % details.city )
            log( 'Country:       %s' % details.country )
            getAvailableFights(details.ID, library)

def allEvents(libraryList):
    for x in sorted(libraryList, key=lambda k: k['path']):
        card = getEventDetails(x['ID'])
        thumbPath = os.path.join(x['path'], 'folder.jpg')
        addDir(card.title, "/getEvent/%s" % card.ID, 1, thumbPath)

def getUniq(seq): 
    seen = []
    result = []
    for item in seq:
        if item in seen: continue
        seen.append(item)
        result.append(item)
    return result

def browseByOrganisation(libraryList):
    promotionList = []
    for x in sorted(libraryList, key=lambda k: k['path']):
        card = getEventDetails(x['ID'])
        if not card.promotion in promotionList:
            promotionList.append(card.promotion)
            promotionThumb = card.promotion + '.jpg'
            thumbPath = os.path.join(__promotionDir__, promotionThumb)
            addDir(card.promotion, "/browsebyorganisation/%s" % card.promotion, 1, thumbPath)

def getEventsByOrganisation(libraryList, organisation):
    eventList = []
    for x in sorted(libraryList, key=lambda k: k['path']):
        card = getEventDetails(x['ID'])
        if card.promotion == organisation:
            thumbPath = os.path.join(x['path'], 'folder.jpg')
            addDir(card.title, "/getEvent/%s" % card.ID, 1, thumbPath)

def browseByFighter(libraryList):
    fighterList = []
    processedFighterList = []
    for x in sorted(libraryList, key=lambda k: k['path']):
        card = getEventDetails(x['ID'])
        for fight in card.fights:
            fighterList.append(fight['fighters'][0])
            fighterList.append(fight['fighters'][1])
    for fighterID in getUniq(fighterList):
        fighter = getFighterDetails(fighterID)
        fighterThumb = fighterID + '.jpg'
        thumbPath = os.path.join(__fighterDir__, fighterThumb)
        processedFighterList.append([fighter.name, fighter.ID, thumbPath])
    for fighterName, fighterID, thumbPath in sorted(processedFighterList):
            addDir(fighterName, "/browsebyfighter/%s" % fighterID, 1, thumbPath)

def getEventsByFighter(libraryList, fighterID):
    eventList = []
    for x in sorted(libraryList, key=lambda k: k['path']):
        card = getEventDetails(x['ID'])
        for fight in card.fights:
            if fighterID in fight['fighters']:
                thumbPath = os.path.join(x['path'], 'folder.jpg')
                addDir(card.title, "/getEvent/%s" % card.ID, 1, thumbPath)
                break

def getEvent(libraryList, eventID):
    fileList = []
    for x in sorted(libraryList, key=lambda k: k['path']):
        if x['ID'] == eventID:
            thumbPath = os.path.join(x['path'], 'folder.jpg')
            card = getEventDetails(x['ID'])
            for root, dirs, files in os.walk(x['path']):
                for vidFile in files:
                    vidFileExt = os.path.splitext(vidFile)[1]
                    vidFilePath = os.path.join(root, vidFile)
                    if vidFileExt in ['.mkv', '.mp4', '.flv', '.avi']:
                        addLink(vidFile, '%s: %s, %s' % (card.date, card.venue, card.city), vidFilePath, thumbPath)
                    else:
                        log('File ignored: %s' % vidFilePath)

if (__name__ == "__main__"):

    for neededDir in [__addondir__, __thumbDir__, __fighterDir__, __promotionDir__, __eventDir__]:
        xbmcvfs.mkdir(neededDir)

    params=get_params()

    libraryList = scanLibrary(__addon__.getSetting("libraryPath"))

    try:
        page = int(urllib.unquote_plus(params["page"]))
    except:
        pass
    
    try:
        path = urllib.unquote_plus(params["path"])
    except:
        pass
    
    if path == "/":
        addDir("Browse by: Organisation", "/browsebyorganisation/", 1, "")
        addDir("Browse by: Fighter", "/browsebyfighter/", 1, "")
        addDir("All Events", "/allevents/", 1, "")
    
    else:
        if path.startswith("/browsebyorganisation/"):
            log("path:%s" % path)
            organisation = path.replace('/browsebyorganisation/','')
            log("organisation:%s" % organisation)
            if organisation == '':
                browseByOrganisation(libraryList)
            else:
                getEventsByOrganisation(libraryList, organisation)
        elif path.startswith("/browsebyfighter/"):
            log("path:%s" % path)
            fighterID = path.replace('/browsebyfighter/','')
            log("fighterID:%s" % fighterID)
            if fighterID == '':
                browseByFighter(libraryList)
            else:
                getEventsByFighter(libraryList, fighterID)
        elif path == "/allevents/":
            allEvents(libraryList)
        elif path.startswith("/getEvent/"):
            eventID = path.replace('/getEvent/','')
            getEvent(libraryList, eventID)
        
        #addDir("> Next Page", path, page+1, "")
    
    xbmcplugin.endOfDirectory(__addonidint__)
