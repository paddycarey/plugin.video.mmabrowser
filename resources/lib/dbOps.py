#!/usr/bin/env python


# import necessary functions
from resources.lib.dbInterface import getData, setData


def getEvents(promotion = '', fighterID = '', searchStr = '', eventID = ''):

    # get events by promotion
    if not promotion == '':
        return getData("SELECT * FROM events WHERE promotion='%s' ORDER BY date" % promotion)
    # get events by fighter
    elif not fighterID == '':
        return getData("SELECT events.* FROM events INNER JOIN fights ON events.eventID=fights.eventID WHERE fighterID='%s' ORDER BY date" % fighterID)
    # search events
    elif not searchStr == '':
        return getData("SELECT * FROM events WHERE (eventID LIKE '%s' OR title LIKE '%s' OR promotion LIKE '%s' OR date LIKE '%s' OR venue LIKE '%s' OR city LIKE '%s') ORDER BY date" % ("%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%"))
    # get single event details
    elif not eventID == '':
        return getData("SELECT * FROM events WHERE eventID='%s'" % eventID)
    # show all events
    else:
        return getData("SELECT * FROM events")


def getFighters(searchStr = ''):
    
    # search fighters
    if not searchStr == '':
        return getData("SELECT DISTINCT fighters.*, COUNT(*) AS cnt FROM fighters INNER JOIN fights ON (fights.fighterID=fighters.fighterID) WHERE (fighters.fighterID LIKE '%s' OR fighters.name LIKE '%s' OR fighters.nickname LIKE '%s' OR fighters.association LIKE '%s' OR fighters.city LIKE '%s' OR fighters.country LIKE '%s') GROUP BY fighters.fighterID ORDER BY fighters.name" % ("%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%", "%" + searchStr + "%"))
    # show all fighters
    else:
        return getData("SELECT DISTINCT fighters.*, COUNT(*) AS cnt FROM fighters INNER JOIN fights ON (fights.fighterID=fighters.fighterID) GROUP BY fighters.fighterID ORDER BY fighters.name")


def getPromotions():

    # get all promotions
    return getData("SELECT DISTINCT promotion FROM events ORDER BY promotion")


def getCounts(promotion = '', fighterID = ''):
    
    # get count of events by promotion
    if not promotion == '':
        return getData("SELECT COUNT(eventID) AS cnt FROM events WHERE promotion='%s'" % promotion)
    # get count of events by promotion
    elif not fighterID == '':
        return getData("SELECT COUNT(eventID) AS cnt FROM fights WHERE fighterID='%s'" % fighterID)
