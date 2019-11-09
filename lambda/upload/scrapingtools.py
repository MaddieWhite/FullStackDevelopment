import requests, json, datetime, sys, re
from bs4 import BeautifulSoup

def request(url):
    try:
        response = requests.get(url)
        return response
    except Exception as err:
        #Add logger here.
        print("Error occured in get occurred: {}".format(err))
    sys.exit()

#This method takes in a regatta dictionary and returns the percetages of regattas sailed in versus attended.
def sailPercentage(regattaDict):
    #Check if the person hasn't sailed any regattas we return a None
    if regattaDict == {}:
        return None

    sailedCounter = 0
    regattaCounter = 0
    for regatta in regattaDict.values():
        regattaCounter = regattaCounter + 1;
        #If they weren't a reserve, add one to the sailedCounter
        if regatta["position"] != "Reserve":
            sailedCounter = sailedCounter + 1;
    if sailedCounter == 0:
        return 0
    return float(sailedCounter)/float(regattaCounter)*100

#This method takes in the regatta dictionary and returns the average finish
def averageFinish(regattaDict):
    #If they have never sailed a regatta we return None
    if regattaDict == {}:
        return None
    finishCounter = 0
    finishTotal = 0

    for regatta in regattaDict.values():
        r_finish = regatta["finish"]
        #If they didn't get a result we continue
        if r_finish == "N/A":
            continue
        #Otherwise, we find all the matches for the DD/DD regex, this can have a problem with certain team race scoring formats
        #But is necessary for when crews sail in two divisions
        results = re.findall(r'[0-9]{1,2}/[0-9]{1,2}', r_finish)
        #For every match we count it as a finish
        for result in results:
            finishCounter += 1
            #We add the left half of the fraction to the total.
            finishTotal += int(re.findall(r'([0-9]{1,2})/', result)[0])
    if finishCounter == 0:
        return None
    return float(finishTotal)/finishCounter

#Takes in a teams UUID and returns a list of sailors uuids.
def roster_finder(uuid, season="f19"):
        page = request("https://scores.collegesailing.org/schools/{}/{}/roster".format(uuid, season))
        content = BeautifulSoup(page.content, 'html.parser')
        roster = []
        #find the tablebody and the find all the player rows
        table = content.find("tbody")
        players = table.find_all("tr")
        #For every player row, we get their href link which is the same as their uuid.
        for player in players:
            #Try catch for the rare time that users on the roster list don't have a roster page.
            try:
                uuid = player.find("a", href = True).get('href')
                uuid = re.search(r'^/sailors/(.*)/$', uuid).group(1)
            except:
                continue
            roster.append(uuid)
        return(roster)

#This method takes in a sailors uuid and returns a dictionary with respective results.
def sailor_scrape(uuid):
    page = request("https://scores.collegesailing.org/sailors/{}/".format(uuid))
    content = BeautifulSoup(page.content, 'html.parser')

    #Setup all output variables
    regattaDict = {}
    eventCounter = 0
    home = None
    grad_year = None
    sailP = None
    averageF = None

    #Before I had tons of output statements, now it's just this.  It removes any datapoints not yet defined when we call it and pushes to database.
    def output():
        dict = {
        'sailor-uuid':uuid,
        'regatta-count':eventCounter,
        'regattas':regattaDict,
        'home': home,
        'grad_year':grad_year,
        'sail-percentage':sailP,
        'average-finish':averageF,
        }
        return dict

    #Check to see if the header field does not exist becuase they haven't sailed a regatta.
    header = content.find(id="content-header")
    if header is None:
        return output()
    home = header.find("ul").find_all("li")[1].find_all("span")[1].text
    grad_year = header.find("ul").find_all("li")[0].find_all("span")[1].text

    #Find all the history tables, there should be one for each season, making sure they have sailed.
    #This may seem redundent to the other if statement but in the case for which a regatta is being currently sailed and they have no other regattas, this is needed.
    history = content.find_all(id="history")
    if history is None:
        return output()

    #Otherwise for every history table, we find all the events in that table.
    for season in history:
        seasonName = season.find('h3').find("a", href=True).get('href')
        seasonUuid = re.search(r'/(.*)/', seasonName).group(1)
        seasonYear = re.search(r'[a-zA-Z]([0-9].*)', seasonUuid).group(1)
        events = season.find('tbody')
        #People who have only sailed one event that is still currently in progress have a history table but no regattas so this checks to see if they have regattas sailed, it doesn't try to find them.
        if events is None:
            continue

        events = events.find_all('tr')
        for event in events:
            #For everyevent, we find the name, location, position and finish and start date.
            tdList = event.find_all('td')
            eventName = event.find_all('span')[0].text
            eventLink = tdList[0].find("a", href=True).get('href')
            eventLocation = tdList[1].text
            eventPosition = tdList[3].text
            eventFinish = tdList[4].text
            startDate = str(datetime.datetime.strptime(tdList[2].text + ", " + seasonYear, "%b %d, %y").date())
            eventCounter+=1
            regattaDict[seasonUuid+"-"+eventName] = {"location":eventLocation, "position":eventPosition, "finish":eventFinish, "start-date":startDate, "link":eventLink}

    #Caculates regatta based data.
    sailP = sailPercentage(regattaDict)
    averageF = averageFinish(regattaDict)
    return output()
