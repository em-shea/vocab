import os
import json
import boto3
from random import randint
from datetime import datetime

import ksuid_service
import list_word_service
import vocab_list_service

eventbridge = boto3.client('events')
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):

    # Select a random word for each level
    # TODO: Check if words were sent in the last 2 weeks - challenge with Level 1 with only 148 words
    todays_words = get_daily_words()

    try:
        # Write to Dynamo
        store_words(todays_words)
    except Exception as e:
        print(e)

    try:
        # Send EventBridge event
        send_event(todays_words)
    except Exception as e:
        print(e)

def get_daily_words():
    print('getting daily words...')

    todays_words = {}

    all_lists = vocab_list_service.get_vocab_lists()

    for list in all_lists:
        try:
            all_words = list_word_service.get_words_in_list(list['list_id'])
            random_number = randint(0,len(all_words)-1)
            random_word = all_words[random_number]
            todays_words[list['list_id']] = random_word
        except Exception as e:
            todays_words[list['list_id']] = None
            print(e)

    print('daily words: ', todays_words)
    return todays_words

def store_words(todays_words):

    for list_id, word_item in todays_words.items():
        date = str(datetime.today().strftime('%Y-%m-%d'))

        word_body = word_item['word']
        # TODO: move removing 'WORD#' on word_id into the list_word_service
        word_body['Word id'] = word_item['word_id'].split('#')[1]

        try:
            response = table.put_item(
                Item={
                    'PK': 'LIST#' + list_id,
                    'SK': 'DATESENT#' + date,
                    'Word': word_body,
                    'GSI1PK': 'DATESENT#' + date,
                    'GSI1SK': 'LIST#' + list_id
                }
            )
            print('stored word: ', word_body)
        except Exception as e:
            print('Error: Failed to store todays word: ', word_body)
            print('DynamoDB response: ', response)
            print(e)

def send_event(todays_words):

    response = eventbridge.put_events(
        Entries=[
            {
                'Source': 'vocab-app',
                'DetailType': 'todays-words-set',
                'Detail': json.dumps({
                    'idempotency-key': str(ksuid_service.generate_ksuid()),
                    'todays-words': todays_words
                    }),
                'EventBusName': os.environ['EVENT_BUS_NAME']
            }
        ]
    )

    return response