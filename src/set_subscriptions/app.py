import os
import json
import boto3
import datetime

import sys
sys.path.insert(0, '/opt')

# region_name specified in order to mock in unit tests
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['DYNAMODB_TABLE_NAME'])

# Set subscriptions and create user if none exists yet
def lambda_handler(event, context):
    # new event payload:
    # {
    #     "user_status":"signed_in", # not_signed_in,
    #     "cognito_id":"123",
    #     "email":"me@testemail.com", # included only if it's a new user subscribing
    #     "char_set_preference":"simplified" # included only if it's a new user subscribing
    #     "set_lists": [
    #         {
    #             "request_type":"subscribe", # unsubscribe
    #             "list_id":"123",
    #             "list_name":"HSK Level 1",
    #             "char_set":"simplified"
    #         },
    #         {
    #             "request_type":"unsubscribe", # subscribe
    #             "list_id":"123",
    #             "list_name":"HSK Level 4",
    #             "char_set":"traditional"
    #         }
    #     ]
    # }

    print(event)

    body = json.loads(event["body"])
    date = str(datetime.datetime.now().isoformat())

    error_message = {
        'statusCode': 502,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : false}'
    }

    if body['user_status'] == "not_signed_in":
        # Create new user in DynamoDB (Cognito on the frontend will catch if the user already exists)
        # TODO: double check if create user is idempotent
        # PutItem creates a new item. If an item with the same key already exists in the table, it is replaced with the new item.
        try:
            create_user(date, body['cognito_id'], body['email'], body['char_set_preference'])
            print(f"Success: Contact created in Dynamo - {body['email'][5:]}, {body['list_name']}.")
        except Exception as e:
            print(f"Error: Failed to create contact in Dynamo - {body['email'][5:]}, {body['list_name']}.")
            print(e)
            return error_message

    for list in body['set_lists']:
        if list['request_type'] == "subscribe":
            # Create new subscription in DynamoDB
            try:
                # TODO: Check if idempotent
                subscribe(date, body['cognito_id'], list)
            except Exception as e:
                return error_message
        if list['request_type'] == "unsubscribe":
            # Unsubscribe user in DynamoDB
            try: 
                unsubscribe(date, body['cognito_id'], list)
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
def create_user(date, cognito_id, email_address, char_set_preference):

    response = table.put_item(
        Item={
                'PK': "USER#" + cognito_id,
                'SK': "USER#" + cognito_id,
                'Email address': email_address,
                'Date created': date,
                'Last login': date,
                'Character set preference': char_set_preference,
                'User alias': "Not set",
                'User alias pinyin': "Not set",
                'GSI1PK': "USER",
                'GSI1SK': "USER#" + cognito_id
            }
        )
    return response

def subscribe(date, cognito_id, list_data):

    response = table.put_item(
        Item={
                'PK': "USER#" + cognito_id,
                'SK': "LIST#" + list_data['list_id'],
                'List name': list_data['list_name'],
                'Date subscribed': date,
                'Status': 'SUBSCRIBED',
                'Character set': list_data['char_set'],
                'GSI1PK': "USER",
                'GSI1SK': "USER#" + cognito_id + "#LIST#" + list_data['list_id'] + "#" + list_data['char_set'].upper()
        },
        ConditionExpression='attribute_not_exists(PK)' # ?
    )

    return response

def unsubscribe(date, cognito_id, list_data): 

    response = table.update_item(
        Item={
                'PK': "USER#" + cognito_id,
                'SK': "LIST#" + list_data['list_id'],
                'List name': list_data['list_name'],
                'Date unsubscribed': date,
                'Status': 'UNSUBSCRIBED',
                'Character set': list_data['char_set'],
                'GSI1PK': "USER",
                'GSI1SK': "USER#" + cognito_id + "#LIST#" + list_data['list_id'] + "#" + list_data['char_set'].upper()
        },
        ConditionExpression='attribute_not_exists(PK)' # ?
    )

    return response
