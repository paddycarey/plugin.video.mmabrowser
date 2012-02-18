#!/usr/bin/env python

"""A set of functions to scrape event and fighter data from sherdog.com"""

__author__      = ['Patrick Carey', 'Jason Harmon']
__copyright__   = 'Copyright 2012 Patrick Carey'
__credits__     = ['Patrick Carey', 'Jason Harmon']
__license__     = 'GPLv2'
__version__     = '0.0.2'

import os
import collections
import socket
from resources.lib.utils import log
from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup

# declare necessary constants for script operation
__fighterURL__ = 'http://www.sherdog.com/fighter/X-%s'
__fighterSearchURL__ = 'http://www.sherdog.com/stats/fightfinder?weight=%s&SearchTxt=%s'
__eventURL__ = 'http://www.sherdog.com/events/X-%s'
__defaultTimeout__ = 60

def getHtml(url):
    
    """
    Retrieve and return remote resource as string
    
    Arguments:
    url -- A string containing the url of a remote page to retrieve
    
    Returns:
    data -- A string containing the contents to the remote page
    """
    
    log('Retrieving url: %s' % url)

    # set default timeout
    socket.setdefaulttimeout(__defaultTimeout__)

    # connect to url using urlopen
    client = urlopen(url)
    
    # read data from page
    data = client.read()
    
    # close connection to url
    client.close()

    log('Retrieved url: %s' % url)

    # return the retrieved data
    return data


def getEventDetails(eventID):
    
    """
    Return event details for a given event ID from sherdog.com's fightfinder.
    
    Arguments:
    eventID -- A String containing the event's numeric event ID from sherdog.com
    
    Returns:
    eventDetails -- A dictionary containing the events details as scraped from sherdog.com.
    
    eventDetails keys:
    ID -- Event's ID
    title -- Event's full title
    promotion -- Promotion which ran the event
    date -- Date of event (YYYY-MM-DD)
    venue -- Event's venue
    city -- City in which event took place
    fights -- A list containing dictionaries (fightDetails[]) with the details of each fight on the event

    fightDetails keys:
    ID -- Fight's ID
    fighter1 -- Sherdog ID for the first fighter
    fighter2 -- Sherdog ID for the second fighter
    winner -- Sherdog ID for the winning fighter
    result -- Method of victory/Type of decision
    referee -- Referee that presided over the fight
    round -- Round in which fight ended
    time -- Time at which final round ended
    """
    
    # initialise empty dict to store event details
    eventDetails = {}
    
    # store event ID in dict
    eventDetails['ID'] = eventID
    
    # generate event url
    url = __eventURL__ % eventID
    
    # retrieve html and initialise beautifulsoup object for parsing
    soup = BeautifulSoup(getHtml(url))
    
    pageTitle = soup.html.head.title.string
    pageTitleArr = pageTitle.split(' - ', 1)	
    # find and store event title in dict
    eventDetails['title'] = pageTitle
    
    # find and store promotion name in dict
    eventDetails['promotion'] = pageTitleArr[0]
    
    # find events date
    tempDate = soup.find("div", {"class" : "authors_info"}).find("span", {"class" : "date"}).string
    
    tempYear = tempDate.split(' ')[2]
    # declare dict to convert month names to numbers
    months = {  'Jan': '01',
                'Feb': '02',
                'Mar': '03',
                'Apr': '04',
                'May': '05',
                'Jun': '06',
                'Jul': '07',
                'Aug': '08',
                'Sep': '09',
                'Oct': '10',
                'Nov': '11',
                'Dec': '12' }
    # get events month and convert to numeric format
    tempMonth = months[tempDate.split(' ')[0]]
    # get events day
    tempDay = "%.2d" % int(tempDate.split(' ')[1].rstrip(','))
    # store event date in dict
    eventDetails['date'] = "%s-%s-%s" % (tempYear, tempMonth, tempDay)
    eventTemp = ''
    try:
        # find and store venue in dict
        eventTemp = soup.find("span", {"class" : "author"}).findAll(text=True)[0].split("\r\n")
        eventDetails['venue'] = eventTemp[0].lstrip().rstrip(",")
    except:
        # store blank string if no venue listed
        eventDetails['venue'] = ''
    
    try:
        # find and store city in dict
        eventDetails['city'] = eventTemp[1].lstrip().rstrip() 
    except:
        # store blank string if no city listed
        eventDetails['city'] = ''
    
    # find list of fights for event
    table = soup.find("div", {"class" : "module_fight_card"})
    
    # initialise empty list to store fightDetails dicts
    eventDetails['fights'] = []

    
    fightDetails = {}
    fights = []
    fightDetails['fighter1'] = soup.find("div", {"class" : "fighter left_side"}).a['href'].rsplit("-", 1)[1]
    fightDetails['fighter2'] = soup.find("div", {"class" : "fighter right_side"}).a['href'].rsplit("-", 1)[1]

    leftResult = ''
    rightResult = ''
    winner = ''
    leftResult = soup.find("div", {"class" : "fighter left_side"}).find("span", {"class" : "final_result win"})
    rightResult = soup.find("div", {"class" : "fighter right_side"}).find("span", {"class" : "final_result win"})
    
    if leftResult != None and leftResult.string == 'win':
        fightDetails['winner'] = fightDetails["fighter1"]
    if rightResult != None and leftResult.string == 'win':
        fightDetails['winner'] = fightDetails["fighter2"]
    
    tempCells =  soup.find("table", {"class" : "resume"}).findAll("td")
    fightDetails['ID'] = int(tempCells[0].findAll(text=True)[1].strip())
    fightDetails['result'] = tempCells[1].findAll(text=True)[1].strip()
    fightDetails['referee'] = tempCells[2].findAll(text=True)[1].strip()
    fightDetails['round'] = tempCells[3].findAll(text=True)[1].strip()
    fightDetails['time'] = tempCells[4].findAll(text=True)[1].strip()
    fights.append(fightDetails)

    # find all rows in the fights table
    rows = soup.find("div", {"class" : "content table"}).findAll("tr")
    
    # set rowcount to 0
    rowcount = 0
        
    # loop through all rows in fights table
    for row in rows:
        
        # ignore first row in table
        if not rowcount == 0:
            
            # find all columns in table
            cols = row.findAll('td')
            
            # initialise empty dict to store fight details
            fightDetails = {}
            
            # find and store fight ID
            fightDetails['ID'] = int(cols[0].string)
            
            # find and store ID for fighter1
            fightDetails['fighter1'] = cols[1].a['href'].rsplit('-', 1)[1]
            # find and store ID for fighter2
            fightDetails['fighter2'] = cols[5].a['href'].rsplit('-', 1)[1]
            
            # check that fight was not a draw
            win = cols[1].find("span").find(text=True)
            if win == 'win':
                # find and store winner ID
                fightDetails['winner'] = fightDetails['fighter1']
            else:
                # store blank string if no winner
                fightDetails['winner'] = ''
            
            # find and store result
            fightDetails['result'] = cols[6].find(text=True).string
            
            # find and store round in which fight ended
            fightDetails['referee'] = cols[6].find("span").string
            
            # find and store round in which fight ended
            fightDetails['round'] = cols[7].string
            
            # find and store end time of fight
            fightDetails['time'] = cols[8].string
            
            # add fightDetails dict to fights list
            fights.append(fightDetails)
        
        # increase rowcount by 1
        rowcount = rowcount + 1

    sort_on = "ID"
    sortFights = [(dict_[sort_on], dict_) for dict_ in fights]
    sortFights.sort()
    eventDetails['fights'] = [dict_ for (key, dict_) in sortFights]
    # return the scraped details
    return eventDetails


def getFighterDetails(fighterID):
    
    """
    Return fighter details for a given fighter ID from sherdog.com's fightfinder.
    
    Arguments:
    fighterID -- A String containing the fighter's numeric ID from sherdog.com
    
    Returns:
    fighterDetails -- A dictionary containing the fighters details as scraped from sherdog.com
    
    fighterDetails keys:
    ID -- Fighter's ID
    name -- Fighter's full name
    nickName -- Fighter's current nickname
    association -- Fighter's current camp/association
    height -- Fighter's height
    weight -- Fighter's weight (in lbs)
    birthDate -- Fighter's date of birth
    city -- Fighter's city of birth
    country -- Fighter's country of birth
    thumbUrl -- URL of fighter image
    """
    
    # initialise empty dict to store fighter details
    fighterDetails = {}
    # set all keys to empty values
    fighterDetails['ID'] = ''
    fighterDetails['name'] = ''
    fighterDetails['nickName'] = ''
    fighterDetails['association'] = ''
    fighterDetails['height'] = ''
    fighterDetails['weight'] = ''
    fighterDetails['birthDate'] = ''
    fighterDetails['city'] = ''
    fighterDetails['country'] = ''
    
    # store fighter ID in dict
    fighterDetails['ID'] = fighterID
    
    # generate fighter url
    url = __fighterURL__ % fighterID
    
    # retrieve html and initialise beautifulsoup object for parsing
    soup = BeautifulSoup(getHtml(url))

    bio = soup.find("div", {"class" : "module bio_fighter"})	
    fighterDetails['name'] = bio.h1.find(text=True)
    try:
        fighterDetails['nickName'] = bio.find("span", {"class" : "nickname"}).em.string
    except Exception:
        fighterDetails['nickName'] = ''
    try:
        fighterDetails['association'] = bio.find("span", {"class" : "item association"}).strong.string
    except Exception:
        fighterDetails['association'] = ''
    try:
        heightTemp = bio.find("span", {"class" : "item height"})
        fighterDetails['height'] = ("%s %s" % (heightTemp.strong.string, heightTemp.findAll(text=True)[3].string)).rstrip()
    except Exception:
        fighterDetails['height'] = ''
    weightTemp = bio.find("span", {"class" : "item weight"})
    fighterDetails['weight'] = ("%s %s" % (weightTemp.strong.string, weightTemp.findAll(text=True)[3].string)).rstrip() 
    fighterDetails['birthDate'] = bio.find("span", {"class" : "item birthday"}).findAll(text=True)[0].rsplit(":")[1].strip()
    try:
        birthpTemp =  bio.find("span", {"class" : "item birthplace"})
        fighterDetails['city'] = birthpTemp.findAll(text=True)[1].strip()
        fighterDetails['country'] = birthpTemp.strong.string
    except Exception:
        fighterDetails['city'] = ''
        fighterDetails['country'] = ''

    # find and store url for fighter image
    fighterDetails['thumbUrl'] = bio.img['src']

    # return scraped details
    return fighterDetails
