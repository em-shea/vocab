import os
import boto3
import tweepy
from random import randint
from boto3.dynamodb.conditions import Key

import review_word_service

idempotency_table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['IDEMPOTENCY_TABLE'])

def lambda_handler(event, context):

    print('event: ', event)
    idempotency_key = event['detail']['idempotency-key']
    time = event['time']
    consumer = "PostTweet"

    try:
        idempotency_response = check_idempotency_key(idempotency_key, consumer)
    except Exception as e:
        print(f"Error: Failed to check idempotency key - {idempotency_key, consumer}.")
        print(e)
        return e
    if len(idempotency_response) == 0:
        try:
            update_idempotency_table(idempotency_key, consumer, time)
        except Exception as e:
            print(f"Error: Failed to update idempotency key - {idempotency_key, consumer}.")
            print(e)
        try:
            word = select_word()
        except Exception as e:
            print(f"Error: Failed to select word - {idempotency_key, consumer}.")
            print(e)
            return e
        try:    
            post_tweet(word)
        except Exception as e:
            print(f"Error: Failed to post tweet - {idempotency_key, consumer}.")
            print(e)
            return e
        print('Tweet sent successfully.')
    else:
        print(f'Tweet already sent for event with idempotency key: {idempotency_key}')
    return

def check_idempotency_key(idempotency_key, consumer):

    response = idempotency_table.query(
        KeyConditionExpression=Key('IdempotencyKey').eq(idempotency_key) & Key('Consumer').eq(consumer)
    )
    print('check key response ', response)
    return response['Items']

def update_idempotency_table(idempotency_key, consumer, time):

    response = idempotency_table.put_item(
        Item = {
                'IdempotencyKey': idempotency_key,
                'Consumer': consumer,
                'Date': time
            }
        )
    print('update key response ', response)
    return response

def select_word():
    todays_words = review_word_service.get_review_words(list_id=None, date_range=0)
    print("words: ", dict(todays_words))
    word_list = []
    # print("print 1", todays_words[0])
    # print("print 2", todays_words[0].values)
    # print("print 3", todays_words[0].keys)
    for value in todays_words.values():
        word_list.append(value[0]['word'])
    print(word_list)
    random_number = randint(0,len(word_list)-1)
    random_word = word_list[random_number]
    print(random_word)
    return random_word

def post_tweet(word):

    tweet = f"Here's a word: {word['word']['simplified']}"

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