import os
import json
import boto3
import datetime
from dataclasses import asdict

import user_service

cognito_client = boto3.client('cognito-idp', region_name = os.environ['AWS_REGION'])
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Unsubscribe function for users that are not signed in
def lambda_handler(event, context):
    print(event)

    error_message = {
        'statusCode': 502,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : false}'
    }

    event_body = json.loads(event["body"])
    date = str(datetime.datetime.now().isoformat())

    if event_body['cognito_id'] == "":
        try:
            user_cognito_id = look_up_cognito_id(event_body)
        except Exception as e:
            print(f'Failed to find user Cognito ID - {event_body}, {e} ')
            return error_message
        event_body['cognito_id'] = user_cognito_id
    
    # No lists passed, unsubscribe all
    if event_body["list"] == "":
        try:
            unsubscribe_all(date, event_body['cognito_id'])
        except Exception as e:
            print(f'Failed to unsubscribe user - {event_body}, {e} ')
            return error_message
    else:
        try:
            unsubscribe_single_list(date, event_body['cognito_id'], event_body['list'])
        except Exception as e:
            print(f'Failed to unsubscribe user - {event_body}, {e} ')
            return error_message
    
    return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Origin': '*',
            },
            'body': '{"success" : true}'
        }

def look_up_cognito_id(event_body):
    print('looking up cognito id...', event_body)
    try:
        response = cognito_client.admin_get_user(
            UserPoolId=os.environ['USER_POOL_ID'],
            Username=event_body['email']
        )
    except Exception as e:
        if e.response['Error']['Code'] == "UserNotFoundException":
            print(f'Error retrieving Cognito Id: user not found for email {event_body["email"]}')
            raise
        else:
            print(f'Error retrieving Cognito Id for user {event_body["email"]}')
            raise

    return response['Username']

def unsubscribe_single_list(date, cognito_id, list_data):
    print(f'unsubscribing user from lists: ', list_data['list_name'], list_data['character_set'])

    response = table.update_item(
        Key = {
            "PK": "USER#" + cognito_id,
            "SK": "LIST#" + list_data['list_id'] + "#" + list_data['character_set'].upper()
        },
        UpdateExpression = "set #s = :status, #d = :date",
        ExpressionAttributeValues = {
            ":status": "unsubscribed",
            ":date": date
        },
        ExpressionAttributeNames = {
            "#s": "Status",
            "#d": "Date unsubscribed"
        },
        ReturnValues = "UPDATED_NEW"
        )

    return response

def unsubscribe_all(date, cognito_id):
    print('unsubscribing user from all lists...')

    user = user_service.get_single_user(cognito_id)
    if user.subscriptions:
        for subscription in user.subscriptions:
            unsubscribe_single_list(date, cognito_id, asdict(subscription))

    return 