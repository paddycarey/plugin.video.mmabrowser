#!/usr/bin/env python

import os
import xbmc
import xbmcaddon
import xbmcvfs

from BeautifulSoup import BeautifulSoup
from resources.lib.utils import *

__addon__             = xbmcaddon.Addon()
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__fighterDir__        = os.path.join(__addondir__, 'fighters')

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
    tempDay = "%.2d" % int(tempDate.split(' ')[1].rstrip(','))
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

    getArtwork(event['promotion'], event['ID'])

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
