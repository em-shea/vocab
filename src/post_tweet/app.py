import os
import boto3
from boto3.dynamodb.conditions import Key

idempotency_table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['IDEMPOTENCY_TABLE'])

def lambda_handler(event, context):

    print('event: ', event)
    idempotency_key = event['Detail']['idempotency-key']

    idempotency_response = check_idempotency_key(idempotency_key)
    if len(idempotency_response) > 0:
        update_idempotency_table(idempotency_key)
        post_tweet(event)
    return

def check_idempotency_key(idempotency_key):

    response = idempotency_table.query(
        KeyConditionExpression=Key('IdempotencyKey').eq(idempotency_key) & Key('Consumer').eq('PostTweet')
    )
    print('dynamo response ', response['Items'])
    return response['Items']

def update_idempotency_table(idempotency_key):

    return

def post_tweet(event):

    return