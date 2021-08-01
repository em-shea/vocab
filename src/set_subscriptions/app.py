import os
import json
import boto3
import datetime

import user_service

# region_name specified in order to mock in unit tests
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['DYNAMODB_TABLE_NAME'])

# Set subscriptions and create user if none exists yet
def lambda_handler(event, context):
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

    try:
        create_user(date, body['cognito_id'], body['email'], body['character_set_preference'])
    except Exception as e:
        print(f"Error: Failed to create user - {body['email'][5:]}, {body['cognito_id']}.")
        print(e)
        return error_message

    # Get a list of ids for all lists the user is currently subscribed to
    user_data = user_service.get_user_data(body['cognito_id'])
    print(user_data['user_data'])
    current_user_lists = user_data['lists']
    if user_data['lists']:
        for list in current_user_lists:
            list['unique_id'] = list['list_id'] + list['character_set']

    # API call will pass all of the users current lists
    # It will call subscribe for all lists and do nothing (ConditionExpression = "attribute_not_exists(PK)")
    # if the subscription is already stored
    # It will check if there are any existing lists not in the new list and it will unsubscribe
    new_list_ids = []
    for list in body['lists']:
        new_list_ids.append(list['list_id'] + list['character_set'])


    # TODO: Currently making an API call per update. Batch updates?
    for list in body['lists']:
        try:
            subscribe(date, body['cognito_id'], list)
            print(f"sub {list['list_id']}, {list['character_set']}")
        except Exception as e:
            print(f"Error: Failed to subscribe user - {body['email'][5:]}, {list['list_id']}.")
            print(e)
            return error_message
    # does existing list check for simplified/traditional?
    for existing_list in current_user_lists:
        if existing_list['unique_id'] not in new_list_ids and existing_list['status'] == "SUBSCRIBED":
            try:
                unsubscribe(date, body['cognito_id'], existing_list)
                print(f"unsub, {existing_list['unique_id']}")
            except Exception as e:
                print(f"Error: Failed to unsubscribe user - {body['email'][5:]}, {existing_list['list_id']}.")
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

def subscribe(date, cognito_id, list_data):

    # PutItem will overwrite an existing item with the same key
    response = table.put_item(
        Item={
                'PK': "USER#" + cognito_id,
                'SK': "LIST#" + list_data['list_id'],
                'List name': list_data['list_name'],
                'Date subscribed': date,
                'Status': 'SUBSCRIBED',
                'Character set': list_data['character_set'],
                'GSI1PK': "USER",
                'GSI1SK': "USER#" + cognito_id + "#LIST#" + list_data['list_id'] + "#" + list_data['character_set'].upper()
        }
    )

    return response

def unsubscribe(date, cognito_id, list_data):

    response = table.update_item(
        Key = {
            "PK": "USER#" + cognito_id,
            "SK": "LIST#" + list_data['list_id']
        },
        UpdateExpression = "set #s = :status, #d = :date",
        ExpressionAttributeValues = {
            ":status": "UNSUBSCRIBED",
            ":date": date
        },
        ExpressionAttributeNames = {
            "#s": "Status",
            "#d": "Date unsubscribed"
        },
        ReturnValues = "UPDATED_NEW"
        )

    return response
