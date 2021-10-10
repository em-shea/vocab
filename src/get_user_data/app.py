import os
import json
import boto3
from boto3.dynamodb.conditions import Key

import user_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['DYNAMODB_TABLE_NAME'])

# For a given user (requires sign-in), return their metadata, subscribed lists, and the past two weeks of quizzes and sentences
def lambda_handler(event, context):
    # print('event', event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    print('user id',cognito_id)
    
    user_data = user_service.get_user_data(cognito_id)

    print('user data', user_data)

    subscribed_lists = []

    # Only return subscribed lists
    for item in user_data['lists']:
        if item['status'] == "subscribed":
            subscribed_lists.append(item)

    user_data['lists'] = subscribed_lists

    print('subscribed ', user_data)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(user_data)
    }