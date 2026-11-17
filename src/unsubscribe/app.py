import os
import json
import boto3
import datetime
from dataclasses import asdict

from botocore.exceptions import ClientError

import user_service

cognito_client = boto3.client('cognito-idp', region_name = os.environ['AWS_REGION'])
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])


class UserNotFound(Exception):
    """No Cognito user exists for the email address given."""


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

    success_message = {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : true}'
    }

    event_body = json.loads(event["body"])
    date = str(datetime.datetime.now().isoformat())

    # Both fields are optional. A caller that knows neither - the bounce handler in
    # receive-ses-email posts nothing but an email address - gets the sensible reading of
    # a bare address: look the user up, and unsubscribe them from every list.
    event_body.setdefault('cognito_id', '')
    event_body.setdefault('list', '')

    if event_body['cognito_id'] == "":
        try:
            user_cognito_id = look_up_cognito_id(event_body)
        except UserNotFound:
            # Nobody is subscribed at this address, so there is nothing to unsubscribe and
            # nothing has gone wrong - anyone may type any address into the public form.
            # Answer exactly as a real unsubscribe does: a distinguishable response would
            # let an anonymous caller test whether a given email is a subscriber, and an
            # 'Error' in the log would raise UnsubscribeErrorAlarm over routine traffic.
            print(f'no Cognito user for {event_body["email"]} - nothing to unsubscribe')
            return success_message
        except Exception as e:
            print(f'Error: Failed to find user Cognito ID - {event_body}, {e} ')
            return error_message
        event_body['cognito_id'] = user_cognito_id

    # No lists passed, unsubscribe all
    if event_body["list"] == "":
        try:
            unsubscribe_all(date, event_body['cognito_id'])
        except Exception as e:
            print(f'Error: Failed to unsubscribe user - {event_body}, {e} ')
            return error_message
    else:
        try:
            unsubscribe_single_list(date, event_body['cognito_id'], event_body['list'])
        except Exception as e:
            print(f'Error: Failed to unsubscribe user - {event_body}, {e} ')
            return error_message
    
    return success_message

def look_up_cognito_id(event_body):
    print('looking up cognito id...', event_body)
    try:
        response = cognito_client.admin_get_user(
            UserPoolId=os.environ['USER_POOL_ID'],
            Username=event_body['email']
        )
    # Only a ClientError carries .response - anything else (a connection failure, a bad
    # env var) propagates as-is and is logged by the caller.
    except ClientError as e:
        if e.response['Error']['Code'] == "UserNotFoundException":
            raise UserNotFound(event_body['email']) from e
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