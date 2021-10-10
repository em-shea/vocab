import os
import boto3
from boto3.dynamodb.conditions import Key

import sys
sys.path.append('../tests/')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['DYNAMODB_TABLE_NAME'])

def get_user_data(cognito_id):

    user_data = pull_user_data(cognito_id)
    response = process_user_data(user_data)

    return response

def pull_user_data(user_id):

    user_key = "USER#" + user_id

    response = table.query(
        KeyConditionExpression=Key('PK').eq(user_key)
    )
    print('dynamo response ', response['Items'])
    return response['Items']

def process_user_data(user_data):

    processed_user_data = {'user_data': {}, 'lists': []}

    #  Loop through all users and subs
    for item in user_data:
        print(item)

        # If Dynamo item is user metadata, add to the main dict
        if 'Email address' in item:
            print('user', item['Email address'])
            processed_user_data['user_data']['email_address'] = item['Email address']
            processed_user_data['user_data']['user_id'] = item['PK'][5:]
            processed_user_data['user_data']['character_set_preference'] = item['Character set preference']
            processed_user_data['user_data']['date_created'] = item['Date created']
            processed_user_data['user_data']['user_alias'] = item['User alias']
            processed_user_data['user_data']['user_alias_pinyin'] = item['User alias pinyin']
            processed_user_data['user_data']['user_alias_emoji'] = item['User alias emoji']

        # If Dynamo item is a list subscription, add the list to the user's lists dict
        if 'List name' in item:
            print('list', item['List name'])
            list_item = {}
            list_item['list_name'] = item['List name']
            list_item['unique_list_id'] = item['SK'][5:]
            # Converting list id from unique id in database (ex, LIST#1ebcad40-bb9e-6ece-a366-acde48001122#SIMPLIFIED)
            if 'SIMPLIFIED' in item['SK']:
                list_item['list_id'] = item['SK'][5:-11]
            if 'TRADITIONAL' in item['SK']:
                list_item['list_id'] = item['SK'][5:-12]
            list_item['character_set'] = item['Character set']
            list_item['status'] = item['Status']
            list_item['date_subscribed'] = item['Date subscribed']
            processed_user_data['lists'].append(list_item)
        # Sort lists by list id to appear in order (Level 1, Level 2, etc.)
        processed_user_data['lists'] = sorted(processed_user_data['lists'], key=lambda k: k['list_id'], reverse=False)

    print('processed_user_data ', processed_user_data)
    return processed_user_data