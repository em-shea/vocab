import os
import boto3
from boto3.dynamodb.conditions import Key

import sys
sys.path.append('../tests/')
print(sys.path)

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

    proccessed_user_data = {'user data': {}, 'lists': []}

    #  Loop through all users and subs
    for item in user_data:
        print(item)

        # If Dynamo item is user metadata, add to the main dict
        if 'Email address' in item:
            print('user', item['Email address'])
            proccessed_user_data['user data']['Email address'] = item['Email address']
            proccessed_user_data['user data']['User id'] = item['PK'][5:]
            proccessed_user_data['user data']['Character set preference'] = item['Character set preference']
            proccessed_user_data['user data']['Date created'] = item['Date created']
            proccessed_user_data['user data']['User alias'] = item['User alias']
            proccessed_user_data['user data']['User alias pinyin'] = item['User alias pinyin']

        # If Dynamo item is a list subscription, add the list to the user's lists dict
        if 'List name' in item:
            print('list', item['List name'])
            list_item = {}
            list_item['List name'] = item['List name']
            list_item['List id'] = item['SK'][5:]
            list_item['Character set'] = item['Character set']
            list_item['Status'] = item['Status']
            list_item['Date subscribed'] = item['Date subscribed']
            proccessed_user_data['lists'].append(list_item)
    print('proccessed_user_data ', proccessed_user_data)
    return proccessed_user_data