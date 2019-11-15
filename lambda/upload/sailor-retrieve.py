## TODO: Something simular to the previous lambda function that returns a dictionary baesd on
import pymysql, requests, re, json, sys, datetime, rds_config
from bs4 import BeautifulSoup
import scrapingtools as st

## TODO: The plan for this class is to return either a forwarding url to the user or an error message.

#Attempt to connect to database.
try:
    conn = pymysql.connect(rds_config.db_host, user=rds_config.db_username, passwd=rds_config.db_password, db=rds_config.db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    print("Connection Issue")
    sys.exit()

def lambda_handler(event, context):
    parameters = event['queryStringParameters']
    return sailor_parse(parameters['uuid'])

#Checks the database to see what operation is needed for the respective sailor.
def sailor_parse(uuid):
    with conn.cursor() as cur:
        #Attempt to retrieve DATETIME coloumn for sailor, it its none, we know the sailor doesn't exit in the database yet.
        command = "SELECT datetime FROM sailors WHERE sailor_uuid='" + uuid + "';"
        cur.execute(command)
        conn.commit()
        response = cur.fetchone()
        #Add if the sailor doesn't exist
        if response is None:
            print("adding")
            single_database_add(uuid)
            return lambdareturn(f"?uuid={uuid}")
        #Then check how old their last update was, if it is older than 7 days, we run an update function, otherwise we do nothing.
        else:
            currentDate = datetime.datetime.now()
            if (response[0] + datetime.timedelta(days=7)) >= currentDate:
                print("updated within 7 days")
                return lambdareturn(f"?uuid={uuid}")
        single_database_update(uuid)
        print("updating")
        return lambdareturn(f"?uuid={uuid}")

#Adds a sailor to the database
## TODO: Error handling for invalid sailor uuids.
def single_database_add(uuid):
    with conn.cursor() as cur:
        #Get the scraped page.
        scraperesult = st.sailor_scrape(uuid)

        #Check to see if the sailors team is in the teams table.
        #The order of the inserts is really important becuase a team needs to exist before we can a sailor to that team.
        team = scraperesult['home']
        cur.execute("""SELECT * FROM teams WHERE team_name=%s """, team)
        conn.commit()
        if cur.fetchone() is None:
            cur.execute("""INSERT INTO teams(team_name) VALUES(%s)""", team)

        #Insert the scraping result into the table first sailors
        scraperesult = st.sailor_scrape(uuid)
        indivStat = scraperesult.copy()
        del indivStat['regattas']
        indivcommand = """INSERT INTO sailors(sailor_uuid, regatta_count, home, grad_year, sail_percent, average_finish) VALUES(%s, %s, %s, %s, %s, %s);"""
        cur.execute(indivcommand, tuple(indivStat[e] for e in indivStat))
        conn.commit()

        #Insert all the regattas
        regattacommand = "INSERT INTO regattas(location, position, finish, startdate, link, sailor_uuid) VALUES(%s, %s, %s, %s, %s, %s)"
        outputDict = []
        for x in scraperesult['regattas']:
            janky = tuple(scraperesult['regattas'][x][e] for e in scraperesult['regattas'][x]) + (uuid,)
            outputDict.append(janky)
        cur.executemany(regattacommand, outputDict)
        conn.commit()

#Updates a sailor's entry in the database.
## TODO: An update that doesn't actually change anything doesn't update the timestamp on the check which is problematic. No clue how to fix.
def single_database_update(uuid):
    with conn.cursor() as cur:
        scraperesult = st.sailor_scrape(uuid)

        #We have to modify the tuple to make it good for the update command.
        sailorInfo = scraperesult.copy()
        del sailorInfo['regattas']
        del sailorInfo['sailor-uuid']
        indivcommand = """UPDATE sailors SET regatta_count=%s, home=%s, grad_year=%s, sail_percent=%s, average_finish=%s WHERE sailor_uuid = %s"""
        cur.execute(indivcommand, tuple(sailorInfo[e] for e in sailorInfo)+(scraperesult['sailor-uuid'],))
        conn.commit()

        #Then for all reqattas, if they don't exist in the regattas table, we add them.
        for x in scraperesult['regattas']:
            checkCommand = "SELECT EXISTS(SELECT * FROM regattas WHERE sailor_uuid=\"" + uuid + "\" AND link=\"" + scraperesult['regattas'][x]['link'] + "\")"
            cur.execute(checkCommand)
            conn.commit()
            if cur.fetchone()[0] == 0:
                regattacommand = "INSERT INTO regattas(location, position, finish, startdate, link, sailor_uuid) VALUES(%s, %s, %s, %s, %s, %s)"
                janky = tuple(scraperesult['regattas'][x][e] for e in scraperesult['regattas'][x]) + (uuid,)
                cur.execute(regattacommand, janky)
                conn.commit()

#lambda return is how we make sure all our returns from lambda are formatted correctly
def lambdareturn(body, status=200):
    return {
    'headers':{"Access-Control-Allow-Origin":"*",},
    "isBase64Encoded": False,
    'statusCode': status,
    'body': json.dumps(body)
    }

print(sailor_parse("thomas-walker"))
