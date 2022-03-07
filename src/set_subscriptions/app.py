import os
import json
import boto3
import datetime
from botocore.exceptions import ClientError

import user_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Set subscriptions (subscribe or unsubscribe) and create user if none exists yet
def lambda_handler(event, context):
    print(event)

    event_body = json.loads(event["body"])
    date = str(datetime.datetime.now().isoformat())

    error_message = {
        'statusCode': 502,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : false}'
    }

    try:
        create_user(date, event_body['cognito_id'], event_body['email'], event_body['character_set_preference'])
    except Exception as e:
        print('error creating user', e)
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            # User already exists, skip
            print(f"User already exists- {event_body['email'][5:]}.")
            pass
        else: 
            print(f"Error: Failed to create user - {event_body['email'][5:]}, {event_body['cognito_id']}.")
            print(e)
            return error_message

    # Get a list of ids for all lists the user is currently subscribed to
    user = user_service.get_single_user(event_body['cognito_id'])
    print(user)

    # API call will pass all of the users current lists
    # It will call subscribe for all lists and do nothing (ConditionExpression = "attribute_not_exists(PK)")
    # if the subscription is already stored
    # It will check if there are any existing lists not in the new list and it will unsubscribe
    new_subscription_list_ids = []
    for subscription in event_body['subscriptions']:
        new_subscription_list_ids.append(subscription['list_id'] + "#" + subscription['character_set'].upper())

    # TODO: Currently making an API call per update. Batch updates?
    for subscription in event_body['subscriptions']:
        try:
            subscribe(date, event_body['cognito_id'], subscription)
            print(f"sub {subscription['list_id']}, {subscription['character_set']}")
        except Exception as e:
            print('error subscribing user', e)
            if e.response['Error']['Code'] == "ConditionalCheckFailedException":
                # Subscription already exists, skip
                print(f"Subcription already exists- {event_body['email'][5:]}, {subscription['list_id']}.")
                pass
            else: 
                print(f"Error: Failed to subscribe user - {event_body['email'][5:]}, {subscription['list_id']}.")
                print(e)
                return error_message
    # does existing list check for simplified/traditional?
    for existing_subscription in user.subscriptions:
        if existing_subscription.unique_list_id not in new_subscription_list_ids and existing_subscription.status == "subscribed":
            try:
                unsubscribe(date, event_body['cognito_id'], existing_subscription)
                print(f"unsub, {existing_subscription.unique_list_id}")
            except Exception as e:
                print('error unsubscribing user', e)
                print(f"Error: Failed to unsubscribe user - {event_body['email'][5:]}, {existing_subscription.list_id}.")
                print(e)
                return error_message

    return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Origin': '*',
            },
            'body': '{"success" : true}'
        }

# Write new contact to Dynamo if it doesn't already exist
def create_user(date, cognito_id, email_address, character_set_preference):

    response = table.put_item(
        Item = {
                'PK': "USER#" + cognito_id,
                'SK': "USER#" + cognito_id,
                'Email address': email_address,
                'Date created': date,
                'Last login': date,
                'Character set preference': character_set_preference,
                'User alias': "Not set",
                'User alias pinyin': "Not set",
                'User alias emoji': "Not set",
                'GSI1PK': "USER",
                'GSI1SK': "USER#" + cognito_id
            },
            ConditionExpression = "attribute_not_exists(PK)"
        )
    return response

def subscribe(date, cognito_id, subscription):

    # PutItem will overwrite an existing item with the same key
    response = table.put_item(
        Item={
                'PK': "USER#" + cognito_id,
                'SK': "LIST#" + subscription['list_id'] + "#" + subscription['character_set'].upper(),
                'List name': subscription['list_name'],
                'Date subscribed': date,
                'Status': 'subscribed',
                'Character set': subscription['character_set'],
                'GSI1PK': "USER",
                'GSI1SK': "USER#" + cognito_id + "#LIST#" + subscription['list_id'] + "#" + subscription['character_set'].upper()
        }
    )

    return response

def unsubscribe(date, cognito_id, subscription):

    response = table.update_item(
        Key = {
            "PK": "USER#" + cognito_id,
            "SK": "LIST#" + subscription.list_id + "#" + subscription.character_set.upper()
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