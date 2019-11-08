import pymysql, requests, re, datetime, json
from bs4 import BeautifulSoup

rds_host  = "sailstat.cgycbijj8kzf.us-east-1.rds.amazonaws.com"
name = "admin"
password = "C6GbBlrJvigSLgatCNS5"
db_name = "indivstats"

#Code to connect to database.
try:
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    print("Fuck")
    sys.exit()

def database_check(uuid):
    with conn.cursor() as cur:
        command = "SELECT EXISTS(SELECT * FROM INDIVSTAT WHERE SAILORUUID='" + uuid + "');"
        cur.execute(command)
        response = str(cur.fetchone())
        if(response == "(0,)"):
            return False
        return True
    conn.close()


def sailor_scrape(uuid):
    with conn.cursor() as cur:
        page = requests.get("https://scores.collegesailing.org/sailors/" + uuid + "/")
        content = BeautifulSoup(page.content, 'html.parser')

        #Setup all output variables
        regattas = {}
        eventCounter = 0
        home = "NULL"
        grad_year = "NULL"
        sailP = "NULL"
        averageF = "NULL"

        #Before I had tons of output statements, not its just this and we remove any datapoints not yet defined when we call it
        def output():
            command = "INSERT INTO INDIVSTAT(SAILORUUID, REGATTACOUNT, HOME, GRADYEAR, SAILP, AVERAGEFINISH) VALUES('" + uuid + "', " + str(eventCounter) + ", \"" +  home + "\", " + str(grad_year) + ", " + str(sailP) + ", " + str(averageF) + ");"
            cur.execute(command)
            conn.commit()
            conn.close()

        #Check to see if the header field does not exist becuase they haven't sailed a regatta.
        header = content.find(id="content-header")
        if header is None:
            output()
        home = header.find("ul").find_all("li")[1].find_all("span")[1].text
        grad_year = header.find("ul").find_all("li")[0].find_all("span")[1].text
        output()
        #Find all the history tables, there should be one for each season, making sure they have sailed.
        #This may seem redundent to the other if statement but in the case for which a regatta is being currently sailed and they have no other regattas, this is needed.
        history = content.find_all(id="history")
        if history is None:
            return

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
                command = "INSERT INTO INDIVREGATTA(LINK, LOCATION, FINISH, STARTDATE, POSITION, SAILORUUID) VALUES('" + eventLink + "', \"" + eventLocation + "\", '" + eventFinish + "', '" + startDate + "', '" + eventPosition + "', '" + uuid + "')"
                print(command)
                cur.execute(command)
                conn.commit()
                # regattas[seasonUuid+"-"+eventName] = {"location":eventLocation, "position":eventPosition, "finish":eventFinish, "start-date":startDate, "link":eventLink}
        #Caculates regatta based data.
        # cur.execute()
sailor_scrape("jessica-williams")
