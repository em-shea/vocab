import os
import boto3
import tweepy
from boto3.dynamodb.conditions import Key

idempotency_table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['IDEMPOTENCY_TABLE'])

def lambda_handler(event, context):

    print('event: ', event)
    idempotency_key = event['detail']['idempotency-key']
    time = event['detail']['time']

    idempotency_response = check_idempotency_key(idempotency_key)
    if len(idempotency_response) > 0:
        update_idempotency_table(idempotency_key, time)
        try:
            post_tweet(event)
        except Exception as e:
            print(e)
    return

def check_idempotency_key(idempotency_key):

    response = idempotency_table.query(
        KeyConditionExpression=Key('IdempotencyKey').eq(idempotency_key) & Key('Consumer').eq('PostTweet')
    )
    print('check key response ', response)
    return response['Items']

def update_idempotency_table(idempotency_key, time):

    response = idempotency_table.put_item(
        Item = {
                'IdempotencyKey': idempotency_key,
                'Consumer': 'PostTweet',
                'Date': time
            }
        )
    print('update key response ', response)
    return response

def post_tweet(event):

    tweet = "Lambda 👋"

    print("Get credentials")
    client = tweepy.Client(
        consumer_key=os.environ['CONSUMER_KEY'],
        consumer_secret=os.environ['CONSUMER_SECRET'],
        access_token=os.environ['ACCESS_TOKEN'],
        access_token_secret=os.environ['ACCESS_TOKEN_SECRET']
    )
    
    response = client.create_tweet(text=tweet)
    print("Twitter response: ", response)

    return {"statusCode": 200, "tweet": tweet}