import pymysql, requests, re, json, sys, datetime, rds_config
## TODO: The plan for this class is to return a json dictionary as its body that we can use ajax to populate HTML.
#Looks like I can make SQL do it: https://mysqlserverteam.com/mysql-8-0-from-sql-tables-to-json-documents-and-back-again/

#Attempt to connect to database.
connection = True
try:
    conn = pymysql.connect(rds_config.db_host, user=rds_config.db_username, passwd=rds_config.db_password, db=rds_config.db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    connection = False

def lambda_handler(event, context):
    parameters = event['queryStringParameters']
    return sailor_request(parameters['column'], parameters['count'], parameters['op'])

def sailor_request(column, count, op):
        #If we can't connect to the database we just return a 500.
    if not connection:
        return lambdareturn("Unable to connect to datebase", 500)
    with conn.cursor() as cur:
        if op.lower() == "desc":
            command  = f"""SELECT * FROM sailors ORDER BY {column} DESC LIMIT {count}"""
            cur.execute(command)
            conn.commit()
            leaderboard = cur.fetchall()
        else:
            command = f"""SELECT * FROM sailors ORDER BY -{column} DESC LIMIT {count}"""
            cur.execute(command)
            conn.commit()
            leaderboard = cur.fetchall()
        return lambdareturn(leaderboard)

#lambda return is how we make sure all our returns from lambda are formatted correctly
def lambdareturn(body, status=200):
    return {
    "headers":{"Access-Control-Allow-Origin":"*",},
    "isBase64Encoded": False,
    "statusCode": status,
    "body": json.dumps(body, indent=4, sort_keys=True, default=str),
    }
