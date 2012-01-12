#!/usr/bin/env python

import os
import sqlite3
import xbmc
import xbmcaddon
import xbmcvfs

from resources.lib.utils import log

### get addon info
__addon__             = xbmcaddon.Addon()
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('profile'))

## initialise database
storageDBPath = os.path.join(__addondir__, 'storage.db')
storageDB = sqlite3.connect(storageDBPath)

def getAllEvents():
    log('Retrieving details of all events from database')
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("SELECT DISTINCT eventID, title, promotion, date, venue, city FROM events ORDER BY date")
        result = cur.fetchall()
    return result

def getAllPromotions():
    log('Retrieving list of all promotions from database')
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("SELECT DISTINCT promotion FROM events ORDER BY promotion")
        result = cur.fetchall()
    return result

def getEventsByPromotion(promotion):
    log('Retrieving details of all events from database for promotion: %s' % promotion)
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("SELECT eventID, title, promotion, date, venue, city FROM events WHERE promotion='%s' ORDER BY date" % promotion)
        result = cur.fetchall()
    return result

def getAllFighters():
    log('Retrieving details of all fighters from database')
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("SELECT DISTINCT fighters.*, COUNT(*) AS cnt FROM fighters INNER JOIN fights ON (fights.fighter1=fighters.fighterID OR fights.fighter2=fighters.fighterID) GROUP BY fighters.fighterID ORDER BY fighters.name")
        result = cur.fetchall()
    return result

def getEventsByFighter(fighterID):
    log('Retrieving details of all events from database for fighter: %s' % fighterID)
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("SELECT DISTINCT events.eventID, events.title, events.promotion, events.date, events.venue, events.city FROM events INNER JOIN fights ON events.eventID=fights.eventID WHERE (fighter1='%s' OR fighter2='%s') ORDER BY date" % (fighterID, fighterID))
        result = cur.fetchall()
    return result

def getEventCount(promotion):
    log('Retrieving count of events in database for promotion: %s' % promotion)
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("SELECT COUNT(DISTINCT eventID) FROM events WHERE promotion='%s'" % promotion)
        result = cur.fetchone()
    return result[0]

def getEvent(eventID):
    log('Retrieving details of event from database: %s' % eventID)
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("SELECT * FROM events WHERE eventID='%s'" % eventID)
        result = cur.fetchone()
    return result

def searchEvents(searchStr):
    log("Searching database for events: %s" % searchStr)
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("SELECT DISTINCT eventID, title, promotion, date, venue, city FROM events WHERE (eventID LIKE '%s' OR title LIKE '%s' OR promotion LIKE '%s' OR date LIKE '%s' OR venue LIKE '%s' OR city LIKE '%s') ORDER BY date" % ("%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%"))
        result = cur.fetchall()
    return result

def searchFighters(searchStr):
    log("Searching database for fighters: %s" % searchStr)
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("SELECT DISTINCT fighters.*, COUNT(*) AS cnt FROM fighters INNER JOIN fights ON (fights.fighter1=fighters.fighterID OR fights.fighter2=fighters.fighterID) WHERE (fighters.fighterID LIKE '%s' OR fighters.name LIKE '%s' OR fighters.nickname LIKE '%s' OR fighters.association LIKE '%s' OR fighters.city LIKE '%s' OR fighters.country LIKE '%s') GROUP BY fighters.fighterID ORDER BY fighters.name" % ("%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%"))
        result = cur.fetchall()
    return result

def getFightersByEvent(eventID):
    log("Retrieving list of fighters for event: %s" % eventID)
    with storageDB:
        cur = storageDB.cursor()
        cur.execute("SELECT fightID, fighters.name FROM fights JOIN fighters ON fights.fighter1=fighters.fighterID WHERE fights.eventID='%s' UNION SELECT fightID, fighters.name FROM fights JOIN fighters ON fights.fighter2=fighters.fighterID WHERE fights.eventID='%s' ORDER BY fights.fightID" % (eventID, eventID))
        result = cur.fetchall()
    fightList = []
    prevFightID = ''
    for halfFight in result:
        if not halfFight[0] == prevFightID:
            fight = "%.2d. %s" % (int(halfFight[0]), halfFight[1])
            prevFightID = halfFight[0]
        else:
            fight = fight + ' vs. %s' % halfFight[1]
            prevFightID = halfFight[0]
            fightList.append(str(fight))
    return sorted(fightList)

