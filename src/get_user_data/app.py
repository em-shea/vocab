import os
import json
import boto3
from dataclasses import asdict
from boto3.dynamodb.conditions import Key

import user_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# For a given user (requires sign-in), return their metadata, subscribed lists, and the past two weeks of quizzes and sentences
def lambda_handler(event, context):
    # print('event', event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    print('user id',cognito_id)
    
    user = user_service.get_single_user(cognito_id)

    # print('user: ', user)

    subscribed_lists = []

    # Only return subscribed lists
    for subscription in user.subscriptions:
        if subscription.status == "subscribed":
            subscribed_lists.append(subscription)

    user.subscriptions = subscribed_lists

    print('subscribed ', user)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(asdict(user))
    }