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

    # update_user_data(cognito_user_id, body)

    return

def update_user_data(cognito_user_id, body):

    response = table.update_item(
        Key={
            'PK': "USER#" + cognito_user_id,
            'SK': "USER#" + cognito_user_id
        },
        UpdateExpression="set 'User alias' = :u, 'User alias pinyin' = :p, 'Character set preference' = :c",
        ExpressionAttributeValues={
            ':u': body['user_alias'],
            ':p': body['user_alias_pinyin'],
            ':c': body['character_set_preference']
        },
        ReturnValues="UPDATED_NEW"
    )

    return response