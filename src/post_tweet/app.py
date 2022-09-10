import os
import boto3
from boto3.dynamodb.conditions import Key

idempotency_table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['IDEMPOTENCY_TABLE'])

def lambda_handler(event, context):

    print('event: ', event)

    check_idempotency_key(event['Detail']['idempotency-key'])


    return

def check_idempotency_key(idempotency_key):

    user_key = "USER#" + cognito_id

    response = idempotency_table.query(
        KeyConditionExpression=Key('IdempotencyKey').eq(user_key) & Key('Consumer').eq('PostTweet')
    )
    print('dynamo response ', response['Items'])
    return response['Items']