import pymysql, requests, re, json, sys, datetime
from bs4 import BeautifulSoup
import scrapingtools as st

rds_host  = "sailstat.cgycbijj8kzf.us-east-1.rds.amazonaws.com"
name = "admin"
password = "C6GbBlrJvigSLgatCNS5"
db_name = "indivstats"

#Code to connect to database.
try:
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    print("Connection Issue")
    sys.exit()

#This checks the database for the sailor, if they do exist we check if their data is a week old.
def sailor_parse(uuid):
    with conn.cursor() as cur:
        #Attempt to retrieve DATETIME coloumn for sailor
        command = "SELECT DATETIME FROM INDIVSTAT WHERE SAILORUUID='" + uuid + "';"
        cur.execute(command)
        response = cur.fetchone()
        #Check if the sailor exists at all
        if response is None:
            single_database_add(uuid)
            return True
        #If they exist check to see if they have been updated in the last week.
        else:
            currentDate = datetime.datetime.now()
            if (response[0] + datetime.timedelta(days=7)) >= currentDate:
                return True
        single_database_update(uuid)
        return True

def single_database_add(uuid):
    with conn.cursor() as cur:
        scraperesult = st.sailor_scrape(uuid)
        indivStat = scraperesult.copy()
        del indivStat['regattas']
        indivcommand = """INSERT INTO INDIVSTAT(SAILORUUID, REGATTACOUNT, HOME, GRADYEAR, SAILP, AVERAGEFINISH) VALUES(%s, %s, %s, %s, %s, %s);"""
        cur.execute(indivcommand, tuple([indivStat[e] for e in indivStat]))
        conn.commit()

        regattacommand = "INSERT INTO INDIVREGATTA(LOCATION, POSITION, FINISH, STARTDATE, LINK, SAILORUUID) VALUES(%s, %s, %s, %s, %s, %s)"
        outputDict = []
        for x in scraperesult['regattas']:
            janky = tuple(scraperesult['regattas'][x][e] for e in scraperesult['regattas'][x]) + (uuid,)
            outputDict.append(janky)
        cur.executemany(regattacommand, outputDict)
        conn.commit()

def single_database_update(uuid):
    with conn.cursor() as cur:
        scraperesult = st.sailor_scrape(uuid)
        indivStat = scraperesult.copy()
        del indivStat['regattas']
        del indivStat['sailor-uuid']
        indivcommand = """UPDATE INDIVSTAT SET REGATTACOUNT=%s, HOME=%s, GRADYEAR=%s, SAILP=%s, AVERAGEFINISH=%s WHERE SAILORUUID = %s"""
        cur.execute(indivcommand, tuple([indivStat[e] for e in indivStat])+(scraperesult['sailor-uuid'],))
        conn.commit()

        for x in scraperesult['regattas']:
            checkCommand = "SELECT EXISTS(SELECT * FROM INDIVREGATTA WHERE SAILORUUID=\"" + uuid + "\" AND LINK=\"" + scraperesult['regattas'][x]['link'] + "\")"
            cur.execute(checkCommand)
            if cur.fetchone()[0] == 0:
                regattacommand = "INSERT INTO INDIVREGATTA(LOCATION, POSITION, FINISH, STARTDATE, LINK, SAILORUUID) VALUES(%s, %s, %s, %s, %s, %s)"
                print("selecting " + x)
                janky = tuple(scraperesult['regattas'][x][e] for e in scraperesult['regattas'][x]) + (uuid,)
                cur.execute(regattacommand, janky)

def sailor_retrieve(uuid):
    with conn.cursor() as cur:
        cur.execute("""SELECT * FROM INDIVSTAT WHERE SAILORUUID=%s""", uuid)
        print(cur.fetchone())
        cur.execute("""SELECT * FROM INDIVREGATTA WHERE SAILORUUID=%s""", uuid)
        print(cur.fetchall())


def lambdareturn(body, status=200):
    return {
    'headers':{"Access-Control-Allow-Origin":"*",},
    "isBase64Encoded": False,
    'statusCode': status,
    'body': json.dumps(body)
    }


sailor_retrieve('thomas-walker')
