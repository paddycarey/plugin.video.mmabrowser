#!/usr/bin/env python

"""A set of functions to scrape event and fighter data from sherdog.com"""

__author__      = 'Patrick Carey'
__copyright__   = 'Copyright 2012 Patrick Carey'
__credits__     = ['Patrick Carey', 'coldbloodedtx']
__license__     = 'GPLv2'
__version__     = '0.0.1'

# import modules necessary for script operation
from BeautifulSoup import BeautifulSoup
from urllib2 import urlopen

# declare necessary constants for script operation
__fightFinderURL__ = 'http://www.sherdog.com/fightfinder/fightfinder.asp?%s'


def getHtml(url):
    
    """
    Retrieve and return remote resource as string
    
    Arguments:
    url -- A string containing the url of a remote page to retrieve
    
    Returns:
    data -- A string containing the contents to the remote page
    """
    
    # connect to url using urlopen
    client = urlopen(url)
    
    # read data from page
    data = client.read()
    
    # close connection to url
    client.close()

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
    round -- Round in which fight ended
    time -- Time at which final round ended
    """
    
    # initialise empty dict to store event details
    eventDetails = {}
    
    # store event ID in dict
    eventDetails['ID'] = eventID
    
    # generate event url
    urlSuffix = 'eventID=%s' % eventDetails['ID']
    url = __fightFinderURL__ % urlSuffix
    
    # retrieve html and initialise beautifulsoup object for parsing
    soup = BeautifulSoup(getHtml(url))
    
    # find and store event title in dict
    eventDetails['title'] = soup.find("div", {"class" : "Txt30Blue Bold SpacerLeft8"}).h1.string
    
    # find and store promotion name in dict
    eventDetails['promotion'] = soup.find("div", {"class" : "Txt13Orange Bold SpacerLeft8"}).a.string
    
    # find events date
    tempDate = soup.find("div", {"class" : "Txt13White Bold SpacerLeft8"}).string
    # get events year
    tempYear = tempDate.split(' ')[2]
    # declare dict to convert month names to numbers
    months = {  'January': '01',
                'February': '02',
                'March': '03',
                'April': '04',
                'May': '05',
                'June': '06',
                'July': '07',
                'August': '08',
                'September': '09',
                'October': '10',
                'November': '11',
                'December': '12' }
    # get events month and convert to numeric format
    tempMonth = months[tempDate.split(' ')[0]]
    # get events day
    tempDay = "%.2d" % int(tempDate.split(' ')[1].rstrip(','))
    # store event date in dict
    eventDetails['date'] = "%s-%s-%s" % (tempYear, tempMonth, tempDay)
    
    try:
        # find and store venue in dict
        eventDetails['venue'] = soup.find("div", {"class" : "Txt13Gray Bold SpacerLeftBottom8"}).findAll(text=True)[0].rstrip().rstrip(',')
    except:
        # store blank string if no venue listed
        eventDetails['venue'] = ''
    
    try:
        # find and store city in dict
        eventDetails['city'] = soup.find("div", {"class" : "Txt13Gray Bold SpacerLeftBottom8"}).findAll(text=True)[1].rstrip().lstrip()
    except:
        # store blank string if no city listed
        eventDetails['city'] = ''
    
    # find list of fights for event
    table = soup.find("table", {"class" : "fight_event_card"})
    
    # initialise empty list to store fightDetails dicts
    eventDetails['fights'] = []
    
    try:
        # find all rows in the fights table
        rows = table.findAll('tr')
        
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
                fightDetails['ID'] = cols[0].string
                
                # find and store ID for fighter1
                fightDetails['fighter1'] = cols[1].a['href'].rsplit('-', 1)[1]
                # find and store ID for fighter2
                fightDetails['fighter2'] = cols[3].a['href'].rsplit('-', 1)[1]
                
                # check that fight was not a draw
                if cols[1].findAll(text=True)[1] == 'Winner':
                    # find and store winner ID
                    fightDetails['winner'] = cols[1].a['href'].rsplit('-', 1)[1]
                else:
                    # store blank string if no winner
                    fightDetails['winner'] = ''
                
                # find and store result
                fightDetails['result'] = cols[4].string
                
                # find and store round in which fight ended
                fightDetails['round'] = cols[5].string
                
                # find and store end time of fight
                fightDetails['time'] = cols[6].string
                
                # add fightDetails dict to fights list
                eventDetails['fights'].append(fightDetails)
            
            # increase rowcount by 1
            rowcount = rowcount + 1
            
    except:
        # skip silently if error encountered
        pass
    
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
    urlSuffix = 'fighterID=%s' % fighterDetails['ID']
    url = __fightFinderURL__ % urlSuffix
    
    # retrieve html and initialise beautifulsoup object for parsing
    soup = BeautifulSoup(getHtml(url))
    
    # find table containing fighter details
    table = soup.find("span", {"id" : "fighter_profile"})
    rows = table.findAll('tr')
    
    # loop over each row in fighter details table
    for row in rows:
        
        # get data from table cell
        infoItem = row.findAll('td')
        
        # skip empty rows
        if infoItem[0].string == None:
            continue
        
        # check if row contains 'name' and store to fighterDetails dict
        elif infoItem[0].string.rstrip(' ').rstrip('\n') == 'Name':
            fighterDetails['name'] = infoItem[1].string.rstrip(' ').rstrip('\n')
        
        # check if row contains 'nickname' and store to fighterDetails dict
        elif infoItem[0].string.rstrip(' ').rstrip('\n') == 'Nick Name':
            fighterDetails['nickName'] = infoItem[1].string.rstrip(' ').rstrip('\n')
        
        # check if row contains 'association' and store to fighterDetails dict
        elif infoItem[0].string.rstrip(' ').rstrip('\n') == 'Association':
            fighterDetails['association'] = infoItem[1].a.string.rstrip(' ').rstrip('\n')
        
        # check if row contains 'height' and store to fighterDetails dict
        elif infoItem[0].string.rstrip(' ').rstrip('\n') == 'Height':
            fighterDetails['height'] = infoItem[1].string.rstrip(' ').rstrip('\n')
        
        # check if row contains 'weight' and store to fighterDetails dict
        elif infoItem[0].string.rstrip(' ').rstrip('\n') == 'Weight':
            fighterDetails['weight'] = infoItem[1].string.rstrip(' ').rstrip('\n')

        # check if row contains 'birth date' and store to fighterDetails dict
        elif infoItem[0].string.rstrip(' ').rstrip('\n') == 'Birth Date':
            fighterDetails['birthDate'] = infoItem[1].string.rstrip(' ').rstrip('\n')

        # check if row contains 'city' and store to fighterDetails dict
        elif infoItem[0].string.rstrip(' ').rstrip('\n') == 'City':
            fighterDetails['city'] = infoItem[1].string.rstrip(' ').rstrip('\n')

        # check if row contains 'country' and store to fighterDetails dict
        elif infoItem[0].string.rstrip(' ').rstrip('\n') == 'Country':
            fighterDetails['country'] = infoItem[1].string.rstrip(' ').rstrip('\n')
        
        # find and store url for fighter image
        fighterDetails['thumbUrl'] = soup.find("span", {"id" : "fighter_picture"}).img['src']
    
    # return scraped details
    return fighterDetails


if __name__ == '__main__':
    
    """Run some tests to ensure scraper is working correctly"""
    
    # import modules necessary for testing
    import unittest
    
    # define class to perform testing
    class TestSherdogScraper(unittest.TestCase):

        def test_fighter(self):
            
            # get fighter details for 2326
            f = getFighterDetails(2326)
            
            # check results of scraper run
            self.assertEqual(f['name'], 'Mirko Filipovic')
            self.assertEqual(f['nickName'], 'Cro Cop')
            self.assertEqual(f['association'], 'Cro Cop Squad Gym')
            self.assertEqual(f['height'], '6\'2" (188cm)')
            self.assertEqual(f['weight'], '227lbs (103kg)')
            self.assertEqual(f['birthDate'], '1974-09-10')
            self.assertEqual(f['city'], 'Zagreb')
            self.assertEqual(f['country'], 'Croatia')
        
        def test_event(self):
            
            # get event details for 18346
            e = getEventDetails(18346)
            
            # check results of scraper run
            self.assertEqual(e['title'], 'UFC 141 - Lesnar vs. Overeem')
            self.assertEqual(e['venue'], 'MGM Grand Garden Arena')
            self.assertEqual(e['city'], 'Las Vegas, Nevada, United States')
            self.assertEqual(e['date'], '2011-12-30')
            self.assertEqual(e['fights'][0]['fighter1'], '25981')
            self.assertEqual(e['fights'][0]['fighter2'], '5185')
            self.assertEqual(e['fights'][0]['fighter1'], e['fights'][0]['winner'])
            self.assertEqual(e['fights'][1]['fighter1'], '24765')
            self.assertEqual(e['fights'][1]['fighter2'], '16555')
            self.assertEqual(e['fights'][1]['fighter1'], e['fights'][1]['winner'])
            self.assertEqual(e['fights'][2]['fighter1'], '16374')
            self.assertEqual(e['fights'][2]['fighter2'], '573')
            self.assertEqual(e['fights'][2]['fighter1'], e['fights'][2]['winner'])
            self.assertEqual(e['fights'][3]['fighter1'], '26070')
            self.assertEqual(e['fights'][3]['fighter2'], '7540')
            self.assertEqual(e['fights'][3]['fighter1'], e['fights'][3]['winner'])
            self.assertEqual(e['fights'][4]['fighter1'], '11884')
            self.assertEqual(e['fights'][4]['fighter2'], '10380')
            self.assertEqual(e['fights'][4]['fighter1'], e['fights'][4]['winner'])
            self.assertEqual(e['fights'][5]['fighter1'], '48046')
            self.assertEqual(e['fights'][5]['fighter2'], '5778')
            self.assertEqual(e['fights'][5]['fighter1'], e['fights'][5]['winner'])
            self.assertEqual(e['fights'][6]['fighter1'], '26162')
            self.assertEqual(e['fights'][6]['fighter2'], '435')
            self.assertEqual(e['fights'][6]['fighter1'], e['fights'][6]['winner'])
            self.assertEqual(e['fights'][7]['fighter1'], '24539')
            self.assertEqual(e['fights'][7]['fighter2'], '4865')
            self.assertEqual(e['fights'][7]['fighter1'], e['fights'][7]['winner'])
            self.assertEqual(e['fights'][8]['fighter1'], '11451')
            self.assertEqual(e['fights'][8]['fighter2'], '15105')
            self.assertEqual(e['fights'][8]['fighter1'], e['fights'][8]['winner'])
            self.assertEqual(e['fights'][9]['fighter1'], '461')
            self.assertEqual(e['fights'][9]['fighter2'], '17522')
            self.assertEqual(e['fights'][9]['fighter1'], e['fights'][9]['winner'])

    # run tests
    unittest.main()
