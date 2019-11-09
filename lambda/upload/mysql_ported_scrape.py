import pymysql, requests, re, datetime, json, sys
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

def database_check(uuid):
    with conn.cursor() as cur:
        command = "SELECT EXISTS(SELECT * FROM INDIVSTAT WHERE SAILORUUID='" + uuid + "');"
        cur.execute(command)
        response = str(cur.fetchone())
        if(response == "(0,)"):
            return False
        return True
    conn.close()


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


for uuid in  st.roster_finder("st-mary"):
    if(not database_check(uuid)):
        single_database_add(uuid)
    else:
        print("already in")

# single_database_add('thomas-walker')
