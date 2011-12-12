#!/usr/bin/env python

# Some links used for testing
# Andre Gusmao http://www.sherdog.com/fightfinder/fightfinder.asp?fighterID=15806
# UFC 98 http://www.sherdog.com/fightfinder/fightfinder.asp?eventID=9529

import os
import socket
import xbmc
import xbmcaddon
import xbmcgui

from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup

### get addon info
__addon__       = xbmcaddon.Addon()
__addonid__     = __addon__.getAddonInfo('id')
__addonname__   = __addon__.getAddonInfo('name')
__author__      = __addon__.getAddonInfo('author')
__version__     = __addon__.getAddonInfo('version')
__localize__    = __addon__.getLocalizedString
__addonpath__   = __addon__.getAddonInfo('path')

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
        message = ('Artwork Downloader: %s' % txt)
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

def rescanLibrary(path):
    pathWalk = os.walk(path)
    log( pathWalk )

class getEventDetails():
    
    def __init__(self, sherdogEventID):

        url = 'http://www.sherdog.com/fightfinder/fightfinder.asp?eventID=%s' % sherdogEventID
        soup = BeautifulSoup(getHtml(url))

        self.ID = sherdogEventID
        self.title = soup.find("div", {"class" : "Txt30Blue Bold SpacerLeft8"}).h1.string
        self.promotion = soup.find("div", {"class" : "Txt13Orange Bold SpacerLeft8"}).a.string
        self.date = soup.find("div", {"class" : "Txt13White Bold SpacerLeft8"}).string
        self.venue = soup.find("div", {"class" : "Txt13Gray Bold SpacerLeftBottom8"}).findAll(text=True)[0].rstrip(',')
        self.city = soup.find("div", {"class" : "Txt13Gray Bold SpacerLeftBottom8"}).findAll(text=True)[1].rstrip('\r\n')
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

class getFighterDetails():
    
    def __init__(self, sherdogFighterID):

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

        url = 'http://www.sherdog.com/fightfinder/fightfinder.asp?fighterID=%s' % sherdogFighterID
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

def getAvailableFights(sherdogFighterID, library):
    for availableCard in library:
        cardID = availableCard['ID']
        cardPath = availableCard['path']
        card = getEventDetails(cardID)
        for fight in card.fights:
            for fighter in fight['fighters']:
                if fighter == sherdogFighterID:
                    log('Fought on: ID: %s Name: %s' % (card.ID, card.title))

def doTestRun():
    # Simple test run
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

if (__name__ == "__main__"):
    library = [{ 'ID' : '9529', 'path' : '/media/raid5/mma_sorted/[2009-05-23] UFC 98: Evans vs. Machida'},{ 'ID' : '17789', 'path' : '/media/raid5/mma_sorted/[2009-05-23] UFC Live: Cruz vs. Johnson'},{ 'ID' : '16309', 'path' : '/media/raid5/mma_sorted/[2011-06-26] UFC Live: Kongo vs. Barry'},{ 'ID' : '8732', 'path' : '/media/raid5/mma_sorted/[2008-12-27] UFC 92: The Ultimate 2008'}]
    doTestRun()
