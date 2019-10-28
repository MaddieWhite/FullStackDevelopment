import requests, json, re, time, random, csv, datetime, boto3, multiprocessing
from bs4 import BeautifulSoup

#Lambda handler that allows for monolith functions accepts single sailor or roster as operations and the uuid for both respectivly
def lambda_handler(event, context):
    if event['op'] == "si":
        return single_person_request(event['uuid'])
    elif event['op'] == 'ro':
        if "season" in event:
            return roster_scrape(event['uuid'], event['season'])
        else:
            return roster_scrape(event['uuid'])

#This function checks the database for the sailor to be already existing and if it does, returns what the database check found.
#Otherwise it calls a new scrape and returns what that finds.
def single_person_request(uuid):
    request = database_check(uuid)
    if request != False:
        return request
    else:
        return sailor_scrape(uuid)

#This function takes in a uuid of the team and the season optionally and creates new lambda invokations for all sailors found.
def roster_scrape(uuid, season="f19"):
    #Invokes seperate lambda functions so that we don't have to rely on one really long invocation for all uuid's found.
    client = boto3.client("lambda")
    for sailor in roster_finder(uuid, season):
        client.invoke(
            FunctionName='single_scraper',
            InvocationType='Event',
            Payload=json.dumps({"uuid":sailor,"op":"si"})
            )

#Takes in a teams UUID and returns a list of sailors uuids.
def roster_finder(uuid, season):
        page = requests.get("https://scores.collegesailing.org/schools/" + uuid + "/" + season + "/roster")
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

#This function takes in the uuid for an individual sailor and returns true, if they exist already or false if they don't
def database_check(uuid):
    dydb = boto3.resource('dynamodb')
    table = dydb.Table("sailor-list")
    try:
        response = table.get_item(Key={"sailor-uuid":uuid})['Item']
    except:
        return False
    # return response #comment this to have the database all update
    return False #uncomment this to have the database always update

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


#This is the main function, scrapes all relevent data for the inputted sailors uuid.
def sailor_scrape(uuid):

    dydb = boto3.resource('dynamodb')
    table = dydb.Table("sailor-list")
    page = requests.get("https://scores.collegesailing.org/sailors/" + uuid + "/")
    content = BeautifulSoup(page.content, 'html.parser')

    #Setup all output variables
    regattas = {}
    eventCounter = 0
    home = None
    grad_year = None
    sailP = None
    averageF = None

    #Before I had tons of output statements, now it's just this.  It removes any datapoints not yet defined when we call it and pushes it to the database.
    def output():
        dict = {
        'sailor-uuid':uuid,
        'regatta-count':eventCounter,
        'regattas':regattas,
        'home': home,
        'grad_year':grad_year,
        'sail-percentage':str(sailP),
        'average-finish':str(averageF),
        'eventLink':eventLink,
        }
        delList = []
        for key in dict:
            if dict[key] == None or dict[key] == 'None':
                delList.append(key)
        for key in delList:
            del dict[key]
        table.put_item(Item=dict)

    #Check to see if the header field does not exist becuase they haven't sailed a regatta.
    header = content.find(id="content-header")
    if header is None:
        output()
    home = header.find("ul").find_all("li")[1].find_all("span")[1].text
    grad_year = header.find("ul").find_all("li")[0].find_all("span")[1].text

    #Find all the history tables, there should be one for each season, making sure they have sailed.
    #This may seem redundent to the other if statement but in the case for which a regatta is being currently sailed and they have no other regattas, this is needed.
    history = content.find_all(id="history")
    if history is None:
        output()

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
            regattas[seasonUuid+"-"+eventName] = {"location":eventLocation, "position":eventPosition, "finish":eventFinish, "start-date":startDate, "link":eventLink}

    #Caculates regatta based data.
    sailP = sailPercentage(regattas)
    averageF = averageFinish(regattas)
    output()
    return(table.get_item(Key={"sailor-uuid":uuid})['Item'])
