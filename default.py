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
__artBaseURL__        = "http://dl.dropbox.com/u/266793/mmaartwork/events/"

### adjust default timeout to stop script hanging
timeout = 20
socket.setdefaulttimeout(timeout)

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

def scanLibrary(scriptPath, libraryPath):

    if scriptPath == '/':
        ## scan libraryPath for directories containing sherdogEventID files
        log('Scanning library for event IDs/paths')
        cur.execute("DROP TABLE IF EXISTS library")
        cur.execute("CREATE TABLE library(ID TEXT, path TEXT)")
        library = []
        idFile = 'sherdogEventID'
        for x in os.walk(libraryPath):
            pathIdFile = os.path.join(x[0], idFile)
            if xbmcvfs.exists(pathIdFile):
                event = {}
                event['ID'] = open(pathIdFile).read()
                event['ID'] = event['ID'].replace('\n', '')
                event['path'] = x[0]
                log('Event ID/path found (%s): %s' % (event['ID'], event['path']))
                library.append(event)
                cur.execute('INSERT INTO library VALUES("%s", "%s")' % (event['ID'], event['path']))
        storageDB.commit()
    else:
        ## loading library from storage
        cur.execute("SELECT * FROM library")
        library = []
        for x in cur.fetchall():
            event = {}
            event['ID'] = x[0]
            event['path'] = x[1]
            library.append(event)
    return library

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

def getEventDetails(sherdogEventID):
    
    """
    This function will retrieve and return all event details from sherdog.com for a given event ID.
    
    name: getEventDetails
    @param sherdogEventID
    @return event
    """

    log('########## Getting event details ##########')
    event = {}
    event['ID'] = sherdogEventID
    log('ID: %s' % event['ID'])
    url = 'http://www.sherdog.com/fightfinder/fightfinder.asp?eventID=%s' % sherdogEventID
    soup = BeautifulSoup(getHtml(url))
    event['title'] = soup.find("div", {"class" : "Txt30Blue Bold SpacerLeft8"}).h1.string
    log('Title: %s' % event['title'])
    event['promotion'] = soup.find("div", {"class" : "Txt13Orange Bold SpacerLeft8"}).a.string
    log('Promotion: %s' % event['promotion'])
    tempDate = soup.find("div", {"class" : "Txt13White Bold SpacerLeft8"}).string
    tempYear = tempDate.split(' ')[2]
    tempDay = tempDate.split(' ')[1].rstrip(',')
    tempMonth = tempDate.split(' ')[0]
    if tempMonth == 'January': tempMonth = '01'
    elif tempMonth == 'February': tempMonth = '02'
    elif tempMonth == 'March': tempMonth = '03'
    elif tempMonth == 'April': tempMonth = '04'
    elif tempMonth == 'May': tempMonth = '05'
    elif tempMonth == 'June': tempMonth = '06'
    elif tempMonth == 'July': tempMonth = '07'
    elif tempMonth == 'August': tempMonth = '08'
    elif tempMonth == 'September': tempMonth = '09'
    elif tempMonth == 'October': tempMonth = '10'
    elif tempMonth == 'November': tempMonth = '11'
    elif tempMonth == 'December': tempMonth = '12'
    event['date'] = "%s-%s-%s" % (tempYear, tempMonth, tempDay)
    log('Date: %s' % event['date'])
    try:
        event['venue'] = soup.find("div", {"class" : "Txt13Gray Bold SpacerLeftBottom8"}).findAll(text=True)[0].rstrip().rstrip(',')
        log('Venue: %s' % event['venue'])
    except:
        event['venue'] = ''
        log('Venue: Not Found')
    try:
        event['city'] = soup.find("div", {"class" : "Txt13Gray Bold SpacerLeftBottom8"}).findAll(text=True)[1].rstrip().lstrip()
        log('City: %s' % event['city'])
    except:
        event['city'] = ''
        log('City: Not Found')
    table = soup.find("table", {"class" : "fight_event_card"})
    event['fights'] = []
    try:
        rows = table.findAll('tr')
        rowcount = 0
        for row in rows:
            if not rowcount == 0:
                cols = row.findAll('td')
                
                fight = {}
                fight['ID'] = cols[0].string
                fight['fighter1'] = cols[1].a['href'].rsplit('-', 1)[1]
                fight['fighter2'] = cols[3].a['href'].rsplit('-', 1)[1]
                if cols[1].findAll(text=True)[1] == 'Winner':
                    fight['winner'] = cols[1].a['href'].rsplit('-', 1)[1]
                else:
                    fight['winner'] = None
                fight['result'] = cols[4].string
                fight['round'] = cols[5].string
                fight['time'] = cols[6].string
                event['fights'].append(fight)
                log('Fight %s: %s vs. %s' % (fight['ID'], fight['fighter1'], fight['fighter2']))
            rowcount = rowcount + 1
    except:
        pass

    eventThumb = event['ID'] + '-poster.jpg'
    eventThumbPath = os.path.join(__thumbDir__, eventThumb)
    if not xbmcvfs.exists(eventThumbPath):
        thumbUrl = __artBaseURL__ + eventThumb
        downloadFile(thumbUrl, eventThumbPath)

    eventFanart = event['ID'] + '-fanart.jpg'
    eventFanartPath = os.path.join(__thumbDir__, eventFanart)
    if not xbmcvfs.exists(eventFanartPath):
        fanartUrl = __artBaseURL__ + eventFanart
        downloadFile(fanartUrl, eventFanartPath)

    log('###### Finished getting event details #####')
    return event

def getFighterDetails(sherdogFighterID):

    """
    This function will retrieve and return all event details from sherdog.com for a given event ID.
    
    name: getEventDetails
    @param sherdogEventID
    @return event
    """

    log('######### Getting fighter details #########')

    fighter = {}
    fighter['ID'] = ''
    fighter['name'] = ''
    fighter['nickName'] = ''
    fighter['association'] = ''
    fighter['height'] = ''
    fighter['weight'] = ''
    fighter['birthYear'] = ''
    fighter['birthDay'] = ''
    fighter['birthMonth'] = ''
    fighter['city'] = ''
    fighter['country'] = ''

    url = 'http://www.sherdog.com/fightfinder/fightfinder.asp?fighterID=%s' % sherdogFighterID

    fighter['ID'] = sherdogFighterID
    log('ID: %s' % fighter['ID'])

    soup = BeautifulSoup(getHtml(url))

    table = soup.find("span", {"id" : "fighter_profile"})
    rows = table.findAll('tr')
    for row in rows:
        infoItem = row.findAll('td')
        if infoItem[0].string == None:
            continue
        if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Name':
            fighter['name'] = infoItem[1].string.rstrip(' ').rstrip('\n')
            log('Name: %s' % fighter['name'])
        if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Nick Name':
            fighter['nickName'] = infoItem[1].string.rstrip(' ').rstrip('\n')
            log('Nickname: %s' % fighter['nickName'])
        if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Association':
            fighter['association'] = infoItem[1].a.string.rstrip(' ').rstrip('\n')
            log('Association: %s' % fighter['association'])
        if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Height':
            fighter['height'] = infoItem[1].string.rstrip(' ').rstrip('\n')
            log('Height: %s' % fighter['height'])
        if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Weight':
            fighter['weight'] = infoItem[1].string.rstrip(' ').rstrip('\n')
            log('Weight: %s' % fighter['weight'])
        if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Birth Date':
            fighter['birthYear'] = infoItem[1].string.rstrip(' ').rstrip('\n').split('-')[0]
            fighter['birthMonth'] = infoItem[1].string.rstrip(' ').rstrip('\n').split('-')[1]
            fighter['birthDay'] = infoItem[1].string.rstrip(' ').rstrip('\n').split('-')[2]
            log('DOB: %s-%s-%s' % (fighter['birthDay'], fighter['birthMonth'], fighter['birthYear']))
        if infoItem[0].string.rstrip(' ').rstrip('\n') == 'City':
            fighter['city'] = infoItem[1].string.rstrip(' ').rstrip('\n')
            log('City: %s' % fighter['city'])
        if infoItem[0].string.rstrip(' ').rstrip('\n') == 'Country':
            fighter['country'] = infoItem[1].string.rstrip(' ').rstrip('\n')
            log('Country: %s' % fighter['country'])
    
    fighterThumb = fighter['ID'] + '.jpg'
    thumbPath = os.path.join(__fighterDir__, fighterThumb)
    if not xbmcvfs.exists(thumbPath):
        thumbUrl = soup.find("span", {"id" : "fighter_picture"}).img['src']
        if not thumbUrl == 'http://www.cdn.sherdog.com/fightfinder/Pictures/blank_fighter.jpg':
            downloadFile(thumbUrl, thumbPath)
    
    log('##### Finished getting fighter details ####')
    return fighter

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

def addLink(name,descr,url,iconimage,fanart):
    if not xbmcvfs.exists(iconimage):
        iconimage=''
    li = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    li.setProperty("IsPlayable", "true")
    li.setInfo( type="Video", infoLabels={ "Title": name , "plot": descr, "plotoutline": descr.replace('\n','')} )
    if xbmcvfs.exists(fanart):
        li.setProperty( "Fanart_Image", fanart )
    xbmcplugin.addDirectoryItem(handle=__addonidint__,url=url,listitem=li, isFolder=False)

def addDir(name,path,page,iconimage,fanart):
    if not xbmcvfs.exists(iconimage):
        iconimage=''
    u=sys.argv[0]+"?path=%s&page=%s"%(path,str(page))
    li=xbmcgui.ListItem(name, iconImage="DefaultFolder.png",thumbnailImage=iconimage)
    li.setInfo( type="Video", infoLabels={ "Title": name })
    #li.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "Date": date } )
    if xbmcvfs.exists(fanart):
        li.setProperty( "Fanart_Image", fanart )
    xbmcplugin.addDirectoryItem(handle=__addonidint__,url=u,listitem=li,isFolder=True)

def allEvents():
    
    cur.execute("SELECT DISTINCT eventID, title, date FROM events ORDER BY date")
    for event in cur.fetchall():
        for x in libraryList:
            if event[0] == x['ID']:
                thumbPath = os.path.join(__thumbDir__, '%s-poster.jpg' % x['ID'])
                fanartPath = os.path.join(__thumbDir__, '%s-fanart.jpg' % x['ID'])
                addDir("%s: %s" % (event[2], event[1]), "/getEvent/%s" % event[0], 1, thumbPath, fanartPath)

def getUniq(seq): 
    seen = []
    result = []
    for item in seq:
        if item in seen: continue
        seen.append(item)
        result.append(item)
    return result

def browseByOrganisation():

    cur.execute("SELECT DISTINCT promotion FROM events ORDER BY promotion")
    for promotion in cur.fetchall():
        promotionThumb = promotion[0] + '-poster.jpg'
        promotionFanart = promotion[0] + '-fanart.jpg'
        thumbPath = os.path.join(__promotionDir__, promotionThumb)
        fanartPath = os.path.join(__promotionDir__, promotionfanart)
        addDir(promotion[0], "/browsebyorganisation/%s" % promotion[0], 1, thumbPath, fanartPath)

def getEventsByOrganisation(organisation):

    cur.execute("SELECT eventID, title, date FROM events WHERE promotion='%s' ORDER BY date" % organisation)
    for event in cur.fetchall():
        for x in libraryList:
            if event[0] == x['ID']:
                thumbPath = os.path.join(__thumbDir__, '%s-poster.jpg' % x['ID'])
                fanartPath = os.path.join(__thumbDir__, '%s-fanart.jpg' % x['ID'])
                addDir("%s: %s" % (event[2], event[1]), "/getEvent/%s" % x['ID'], 1, thumbPath, fanartPath)

def browseByFighter():

    cur.execute("SELECT DISTINCT fighterID, name FROM fighters ORDER BY name")
    for fighter in cur.fetchall():
        fighterThumb = fighter[0] + '.jpg'
        thumbPath = os.path.join(__fighterDir__, fighterThumb)
        fanartPath = ''
        addDir(fighter[1], "/browsebyfighter/%s" % fighter[0], 1, thumbPath, fanartPath)

def getEventsByFighter(fighterID):

    cur.execute("SELECT DISTINCT eventID FROM fights WHERE (fighter1='%s' OR fighter2='%s')" % (fighterID, fighterID))
    events = []
    for eventID in cur.fetchall():
        eventDict = {}
        cur.execute("SELECT eventID, title, date FROM events WHERE ID='%s'" % eventID)
        event = cur.fetchone()
        for x in libraryList:
            if x['ID'] == event[0]:
                eventDict['thumbPath'] = os.path.join(__thumbDir__, '%s-poster.jpg' % x['ID'])
                eventDict['fanartPath'] = os.path.join(__thumbDir__, '%s-fanart.jpg' % x['ID'])
                break
        eventDict['ID'] = event[0]
        eventDict['title'] = event[1]
        eventDict['date'] = event[2]
        events.append(eventDict)
    for event in sorted(events, key=lambda k: k['date']):
        addDir("%s: %s" % (event['date'], event['title']), "/getEvent/%s" % event['ID'], 1, event['thumbPath'], eventDict['fanartPath'])

def getEvent(eventID):
    
    cur.execute("SELECT * FROM events WHERE eventID='%s'" % eventID)
    event = cur.fetchone()
    for x in libraryList:
        if event[0] == x['ID']:
            thumbPath = os.path.join(__thumbDir__, '%s-poster.jpg' % x['ID'])
            fanartPath = os.path.join(__thumbDir__, '%s-fanart.jpg' % x['ID'])
            for root, dirs, files in os.walk(x['path']):
                for vidFile in files:
                    vidFileExt = os.path.splitext(vidFile)[1]
                    vidFilePath = os.path.join(root, vidFile)
                    if vidFileExt in ['.mkv', '.mp4', '.flv', '.avi']:
                        addLink(vidFile, '%s: %s, %s' % (event[3], event[4], event[5]), vidFilePath, thumbPath, fanartPath)
                    else:
                        log('File ignored: %s' % vidFilePath)

if (__name__ == "__main__"):

    ## parse plugin arguments
    params = get_params()

    ## get page number
    try:
        page = int(urllib.unquote_plus(params["page"]))
    except:
        page = 1

    ## get path
    try:
        path = urllib.unquote_plus(params["path"])
    except:
        path = "/"

    ## create directories needed for script operation
    for neededDir in [__addondir__, __thumbDir__, __fighterDir__, __promotionDir__]:
        xbmcvfs.mkdir(neededDir)

    ## initialise persistent storage
    storageDBPath = os.path.join(__addondir__, 'storage.db')
    storageDB = sqlite3.connect(storageDBPath)
    cur = storageDB.cursor()

    ## retrieve current list of events in libraryPath
    libraryList = scanLibrary(path, __addon__.getSetting("libraryPath"))

    try:
        ##attempt to load tables from storage
        cur.execute("SELECT * from events")
        cur.execute("SELECT * from fights")
        cur.execute("SELECT * from fighters")
    except sqlite3.Error, e:
        __addon__.setSetting(id="forceFullRescan", value='true')
        log('SQLite Error: %s' % e.args[0])
        log('Unable to load event list from storage: rescanning')
        log('Performing full event scan: THIS MAY TAKE A VERY LONG TIME', xbmc.LOGWARNING)
    if __addon__.getSetting("forceFullRescan") == 'true':
        cur.execute("DROP TABLE IF EXISTS events")
        cur.execute("CREATE TABLE events(eventID TEXT, title TEXT, promotion TEXT, date TEXT, venue TEXT, city TEXT)")
        cur.execute("DROP TABLE IF EXISTS fights")
        cur.execute("CREATE TABLE fights(eventID TEXT, fightID TEXT, fighter1 TEXT, fighter2 TEXT, winner TEXT, result TEXT, round TEXT, time TEXT)")
        cur.execute("DROP TABLE IF EXISTS fighters")
        cur.execute("CREATE TABLE fighters(fighterID TEXT, name TEXT, nickName TEXT, association TEXT, height TEXT, weight TEXT, birthYear TEXT, birthMonth TEXT, birthDay TEXT, city TEXT, country TEXT)")
        __addon__.setSetting(id="forceFullRescan", value='false')
    ## for every new event in library retrieve details from sherdog.com
    for libraryItem in libraryList:
        scannedID = unicode(libraryItem['ID'])
        cur.execute("SELECT DISTINCT eventID FROM events")
        storedIDs = cur.fetchall()
        if not (scannedID,) in storedIDs:
            try:
                event = getEventDetails(libraryItem['ID'])
                cur.execute("INSERT INTO events VALUES('%s', '%s', '%s', '%s', '%s', '%s')" % (event['ID'], event['title'].replace('\'', ''), event['promotion'].replace('\'', ''), event['date'], event['venue'].replace('\'', ''), event['city'].replace('\'', '')))
                for fight in event['fights']:
                    cur.execute("INSERT INTO fights VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (event['ID'], fight['ID'], fight['fighter1'], fight['fighter2'], fight['winner'], fight['result'].replace('\'', ''), fight['round'].replace('\'', ''), fight['time'].replace('\'', '')))
                    cur.execute("SELECT fighterID from fighters")
                    fighters = cur.fetchall()
                    for fighter in [fight['fighter1'], fight['fighter2']]:
                        if not (fighter,) in fighters:
                            fighterDetails = getFighterDetails(fighter)
                            cur.execute("INSERT INTO fighters VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (fighterDetails['ID'], fighterDetails['name'].replace('\'', ''), fighterDetails['nickName'].replace('\'', ''), fighterDetails['association'].replace('\'', ''), fighterDetails['height'].replace('\'', ''), fighterDetails['weight'].replace('\'', ''), fighterDetails['birthYear'], fighterDetails['birthMonth'], fighterDetails['birthDay'], fighterDetails['city'].replace('\'', ''), fighterDetails['country'].replace('\'', '')))
                    storageDB.commit()
            except:
                log('Error adding event to database: %s' % libraryItem['ID'])
                log('Rolling back database to clean state')
                storageDB.rollback()
                sys.exit(1)

    ## check path and generate desired list
    if path == "/":
        ## populate main menu
        addDir("Browse by: Organisation", "/browsebyorganisation/", 1, "")
        addDir("Browse by: Fighter", "/browsebyfighter/", 1, "")
        addDir("All Events", "/allevents/", 1, "")
    
    else:
        if path.startswith("/browsebyorganisation/"):
            log("path:%s" % path)
            organisation = path.replace('/browsebyorganisation/','')
            log("organisation:%s" % organisation)
            if organisation == '':
                ## populate list of organisations
                browseByOrganisation()
            else:
                ## populate list of events for a given organisation
                getEventsByOrganisation(organisation)
        elif path.startswith("/browsebyfighter/"):
            log("path:%s" % path)
            fighterID = path.replace('/browsebyfighter/','')
            log("fighterID:%s" % fighterID)
            if fighterID == '':
                ## populate list of fighters
                browseByFighter()
            else:
                ## populate list of all events a given fighter has fought in
                getEventsByFighter(fighterID)
        elif path == "/allevents/":
            ## populate list of all events
            allEvents()
        elif path.startswith("/getEvent/"):
            eventID = path.replace('/getEvent/','')
            ## populate list of all video files for a given event
            getEvent(eventID)

        ## add 'Next Page' button to bottom of list
        #addDir("> Next Page", path, page+1, "")

    ## close persistent storage file
    storageDB.close()
    ## finish adding items to list and display
    xbmcplugin.endOfDirectory(__addonidint__)
