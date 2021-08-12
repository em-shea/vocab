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
    
    processed_user_data = user_service.get_user_data(cognito_id)

    print('processed user data', processed_user_data)

    # Only return SUBSCRIBED lists
    for item in processed_user_data['lists']:
        if item['status'] == "UNSUBSCRIBED":
            processed_user_data['lists'].remove(item)

    print('removed ', processed_user_data)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(processed_user_data)
    }