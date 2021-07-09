import os
import json
import boto3
from boto3.dynamodb.conditions import Key

import sys
sys.path.insert(0, '/opt')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['DYNAMODB_TABLE_NAME'])

# For a given user (requires sign-in), update user metadata
def lambda_handler(event, context):
    # payload = {
    #     'user_alias': '小王 📙',
    #     'user_alias_pinyin': 'xiǎo wáng',
    #     'character_set_preference': 'traditional'
    # }

    print('event', event)
    cognito_user_id = event['requestContext']['authorizer']['claims']['sub']
    print('user id',cognito_user_id)

    body = json.loads(event["body"])

    update_user_data(body)

    return

def update_user_data(body):

    print(body)
    return