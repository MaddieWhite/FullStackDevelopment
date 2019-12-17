import pymysql, requests, re, json, sys, datetime, rds_config

#Attempt to connect to database.
connection = True
try:
    conn = pymysql.connect(rds_config.db_host, user=rds_config.db_username, passwd=rds_config.db_password, db=rds_config.db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    connection = False

def lambda_handler(event, context):
    parameters = event['queryStringParameters']
    return column_request(parameters['table'], parameters['column'], parameters['condition'])

def column_request(table, column, condition):
        #If we can't connect to the database we just return a 500.
    if not connection:
        return lambdareturn("Unable to connect to datebase", 500)
    with conn.cursor() as cur:
        #Retrive the sailors data already as json.
        if condition == "*":
            cur.execute(f"""SELECT JSON_ARRAYAGG({column}) FROM {table}""")
            conn.commit()
        else:
            cur.execute(f"""SELECT JSON_ARRAYAGG({column}) FROM {table} WHERE {condition}""")
            conn.commit()
        try:
            response = json.loads(cur.fetchone()[0])
        except:
            return lambdareturn("Column or table not found", 400)
        return lambdareturn(response)

#lambda return is how we make sure all our returns from lambda are formatted correctly
def lambdareturn(body, status=200):
    return {
    "headers":{"Access-Control-Allow-Origin":"*",},
    "isBase64Encoded": False,
    "statusCode": status,
    "body": json.dumps(body)
    }
