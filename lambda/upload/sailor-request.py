import pymysql, requests, re, json, sys, datetime, rds_config

#Attempt to connect to database.
connection = True
try:
    conn = pymysql.connect(rds_config.db_host, user=rds_config.db_username, passwd=rds_config.db_password, db=rds_config.db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    connection = False

def lambda_handler(event, context):
    parameters = event['queryStringParameters']
    return sailor_request(parameters['uuid'])

def sailor_request(uuid):
        #If we can't connect to the database we just return a 500.
    if not connection:
        return lambdareturn("Unable to connect to datebase", 500)
    with conn.cursor() as cur:
        #Retrive the sailors data already as json.
        cur.execute("""SELECT JSON_OBJECT("sailor-uuid", sailor_uuid, "average_finish", average_finish, "grad_year", CONVERT(grad_year, CHAR), "regatta_count", regatta_count, "sail_percentage", sail_percent, "home", home, "seconds_traveled", second_traveled, "meters_traveled", meters_traveled) FROM sailors WHERE sailor_uuid=%s""", uuid)
        conn.commit()
        try:
            sailorDict = json.loads(cur.fetchone()[0])
        except:
            return lambdareturn("Sailor not found", 400)
        #Retrieve the regattas as a array of json objects
        cur.execute("""SELECT JSON_ARRAYAGG(JSON_OBJECT(p.link, JSON_OBJECT("location", p.location , "finish", p.finish, "start-date", p.startdate, "position", p.position))) FROM regattas p WHERE sailor_uuid=%s""", uuid)
        conn.commit()
        regattaStats = json.loads(cur.fetchone()[0])
        #Combine all the dictionaries in the array
        save = {"regattas": {k: v for d in regattaStats for k, v in d.items()}}
        #Combine the two dictionaries
        sailorDict.update(save)
        return lambdareturn(sailorDict)

#lambda return is how we make sure all our returns from lambda are formatted correctly
def lambdareturn(body, status=200):
    return {
    "headers":{"Access-Control-Allow-Origin":"*",},
    "isBase64Encoded": False,
    "statusCode": status,
    "body": json.dumps(body)
    }
