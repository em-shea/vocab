import os
import json
import boto3
from random import randint
from datetime import datetime

import ksuid_service
import list_word_service
import user_service
import vocab_list_service

eventbridge = boto3.client('events')
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):

    # Select a random word for each level
    # TODO: Check if words were sent in the last 2 weeks - challenge with Level 1 with only 148 words
    todays_words = set_daily_words()

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

def set_daily_words():
    print('selecting todays words...')

    todays_words = {}

    for list in get_lists_needing_a_daily_word():
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

def get_lists_needing_a_daily_word():
    """Curated lists, plus user lists that someone is actually subscribed to.

    This job does one full-list query and one write per list in a 128MB/120s
    function. Curated lists are always included so the public home page and the
    sample endpoint stay populated even with no subscribers; user-created lists
    are only worth a daily word once somebody reads them, which keeps the fan-out
    bounded by demand rather than by how many lists have ever been uploaded.
    """
    all_lists = vocab_list_service.get_vocab_lists()

    try:
        subscribed_list_ids = user_service.get_subscribed_list_ids()
    except Exception as e:
        # Degrade to setting a word for every list rather than skipping lists that
        # may well have subscribers
        print('Error: Failed to read subscribed lists, falling back to all lists.')
        print(e)
        return all_lists

    lists_needing_a_word = [
        l for l in all_lists
        if l['created_by'] == vocab_list_service.CREATED_BY_ADMIN
        or l['list_id'] in subscribed_list_ids
    ]

    print(f"{len(lists_needing_a_word)} of {len(all_lists)} lists need a word today.")
    return lists_needing_a_word

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
                    'idempotency-key': str(ksuid_service.generate_ksuid())
                    # 'todays-words': todays_words
                    }),
                'EventBusName': os.environ['EVENT_BUS_NAME']
            }
        ]
    )

    print('Put events response: ', response)
    return response