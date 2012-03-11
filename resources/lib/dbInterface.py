#!/usr/bin/env python

# import necessary modules
import os
import sqlite3
import traceback
import xbmc
import xbmcaddon

# import logging function
from resources.lib.utils import log

### get addon info
__addon__             = xbmcaddon.Addon()
__addondir__          = xbmc.translatePath(__addon__.getAddonInfo('profile'))

# current database version (see resources/docs/db-changelog.txt)
__dbVersion__ = 0.2

# path to database file
storageDBPath = os.path.join(__addondir__, 'storage-%s.db' % __dbVersion__)

# connect to database
storageDB = sqlite3.connect(storageDBPath)


def getData(sqlQuery):
    
    # print query to log
    log('SQL (getData): Running Query: %s' % sqlQuery)
    
    with storageDB:
        
        # use dictionary cursor instead of standard cursor
        storageDB.row_factory = sqlite3.Row
        
        # get cursor
        cur = storageDB.cursor()
        
        # perform sql query
        cur.execute(sqlQuery)
        
        # get results of sql query
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append(row)

    # return results of query
    return results


def setData(sqlQuery = '', deferCommit = False):
    
    # print query to log
    log('SQL (setData): Running Query: %s' % sqlQuery)

    with storageDB:

        try:
    
            # get cursor
            cur = storageDB.cursor()  
            
            if not sqlQuery == '':
                # perform sql query
                cur.execute(sqlQuery)
            
            if not deferCommit:
                # commit to database
                storageDB.commit()
        
        except:
        
            # print traceback to log
            log(str(traceback.format_exc()))
            
            # print error messages to log
            log('SQL (setData): Error Executing Query')
            log('Rolling back database to clean state')
            
            # rollback any uncommited queries
            storageDB.rollback()
            
            # return false on error
            retStatus = False
        
        else:
            
            # return true if commit successful
            retStatus = True
        
    return retStatus

    
