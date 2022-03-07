import os
import json
import boto3
import datetime
from boto3.dynamodb.conditions import Key

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# For a given user (requires sign-in), update user metadata
def lambda_handler(event, context):

    print('event', event)
    cognito_user_id = event['requestContext']['authorizer']['claims']['sub']
    print('user id',cognito_user_id)

    error_message = {
        'statusCode': 502,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : false}'
    }

    try:
        update_last_login(cognito_user_id)
    except Exception as e:
        print(f"Error: Failed to update last login - {cognito_user_id}.")
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

def update_last_login(cognito_user_id):

    response = table.update_item(
        Key={
            'PK': "USER#" + cognito_user_id,
            'SK': "USER#" + cognito_user_id
        },
        UpdateExpression="set #login = :u",
        ExpressionAttributeNames={
            '#login': 'Last login'
        },
        ExpressionAttributeValues={
            ':u': str(datetime.datetime.now().isoformat())
        },
        ReturnValues="UPDATED_NEW"
    )

    return response