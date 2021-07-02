import os
import json
import boto3
import datetime

import sys
sys.path.insert(0, '/opt')

# region_name specified in order to mock in unit tests
# dynamo_client = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
# table = dynamo_client.Table(os.environ['DYNAMODB_TABLE_NAME'])
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['DYNAMODB_TABLE_NAME'])

# Create a new subscription and/or user in DynamoDB
def lambda_handler(event, context):

    print(event)

    body = json.loads(event["body"])

    # Extract relevant user details
    # Example event body: {"subType": "newUser", "cognitoId": "123", "email": "me@testemail.com", "listId": "123", "listName": "HSK Level 1", "charSet": "simplified"}
    partial_email = body['email'][0:5]
    list_id = body['listId']

    error_message = {
        'statusCode': 502,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : false}'
    }

    if body['subType'] == "newUser":
        # Create new user in DynamoDB
        try:
            create_user(body['cognitoId'], body['email'], body['charSet'])
            print(f"Success: Contact created in Dynamo - {partial_email}, {list_id}.")
        except Exception as e:
            print(f"Error: Failed to create contact in Dynamo - {partial_email}, {list_id}.")
            print(e)
            return error_message

    # Create new subscription in DynamoDB
    try: 
        create_subscription(body['cognitoId'], body['charSet'], body['listId'], body['listName'])
    except Exception as e:
        return error_message

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : true}'
    }

# Write new contact to Dynamo
def create_user(cognito_id, email_address, char_set):
    date = str(datetime.datetime.now().isoformat())

    response = table.put_item(
        Item={
                'PK': "USER#" + cognito_id,
                'SK': "USER#" + cognito_id,
                'Email address': email_address,
                'Date created': date,
                'Last login': date,
                'Character set preference': char_set,
                'GSI1PK': "USER",
                'GSI1SK': "USER#" + cognito_id
            }
        )
    return response

def create_subscription(cognito_id, char_set, list_id, list_name):
    date = str(datetime.datetime.now().isoformat())

    response = table.put_item(
        Item={
                'PK': "USER#" + cognito_id,
                'SK': "LIST#" + list_id,
                'List name': list_name,
                'Date subscribed': date,
                'Status': 'SUBSCRIBED',
                'Character set': char_set,
                'GSI1PK': "USER",
                'GSI1SK': "USER#" + cognito_id + "#LIST#" + list_id + "#" + char_set.upper()
        },
        ConditionExpression='attribute_not_exists(PK)'
        )
    return response
