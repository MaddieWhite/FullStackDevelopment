import pymysql, requests, re, json, sys, datetime, rds_config, boto3
import scrapingtools as st
## TODO: The plan for this class is to return a json dictionary as its body that we can use ajax to populate HTML.
#Looks like I can make SQL do it: https://mysqlserverteam.com/mysql-8-0-from-sql-tables-to-json-documents-and-back-again/

lambda_client = boto3.client('lambda')

#Attempt to connect to database.
def lambda_handler(event, context):
    parameters = event['queryStringParameters']
    return populate(parameters['team'], parameters['season'])

def populate(team, season):
    #If we can't connect to the database we just return a 500.
    roster = st.roster_finder(team, season)
    body = ""

    for sailor in roster:
        response = lambda_client.invoke(FunctionName = 'sailor-retrieve', Payload = json.dumps({
            "httpMethod": "GET",
            "isBase64Encoded": "true",
            "queryStringParameters": {
            "uuid": sailor
            }
        }))
        output = response['Payload'].read().decode("utf-8")
        print(output)
        body += str(json.loads(output))

    return lambdareturn({
        "roster": roster,
        "body": body
    }, 200)


#lambda return is how we make sure all our returns from lambda are formatted correctly
def lambdareturn(body, status=200):
    return {
    "headers":{"Access-Control-Allow-Origin":"*",},
    "isBase64Encoded": False,
    "statusCode": status,
    "body": json.dumps(body),
    }
