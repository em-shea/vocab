import os
import json
import boto3
from boto3.dynamodb.conditions import Key

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# For a given user (requires sign-in), update user metadata
def lambda_handler(event, context):

    print('event', event)
    cognito_user_id = event['requestContext']['authorizer']['claims']['sub']
    print('user id',cognito_user_id)

    body = json.loads(event["body"])

    error_message = {
        'statusCode': 502,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : false}'
    }

    try:
        update_user_data(cognito_user_id, body)
    except Exception as e:
        print(f"Error: Failed to update user data - {cognito_user_id}.")
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

def update_user_data(cognito_user_id, body):

    response = table.update_item(
        Key={
            'PK': "USER#" + cognito_user_id,
            'SK': "USER#" + cognito_user_id
        },
        UpdateExpression="set #alias = :u, #pinyin = :p, #emoji = :e, #char = :c",
        ExpressionAttributeNames={
            '#alias': 'User alias',
            '#pinyin': 'User alias pinyin',
            '#emoji': 'User alias emoji',
            '#char': 'Character set preference'
        },
        ExpressionAttributeValues={
            ':u': body['user_alias'],
            ':p': body['user_alias_pinyin'],
            ':e': body['user_alias_emoji'],
            ':c': body['character_set_preference']
        },
        ReturnValues="UPDATED_NEW"
    )

    return response