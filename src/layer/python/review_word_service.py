import os
import json
import boto3
from datetime import datetime
from datetime import timedelta
from dataclasses import asdict
from collections import defaultdict
from models import ReviewWord, Word
from boto3.dynamodb.conditions import Key

import vocab_list_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

def get_review_words(list_id, date_range, vocab_lists=None):

    todays_date = format_date(datetime.today())

    # Read the list set per call rather than once at module import. A module-level
    # cache is frozen for the life of a warm Lambda container, so a newly created
    # list would stay invisible until the container recycled.
    # Callers pass vocab_lists to control visibility (e.g. public-only) and to avoid
    # re-querying when they already hold the set.
    if vocab_lists is None:
        vocab_lists = vocab_list_service.get_vocab_lists()

    filtered_lists = [l for l in vocab_lists if (list_id is None or l['list_id'] == list_id)]

    from_date = format_date(datetime.today() - timedelta(days=int(7)))
    if date_range is not None:
        from_date = format_date(datetime.today() - timedelta(days=int(date_range)))

    review_words = defaultdict(list)
    for vocab_list in filtered_lists:
        word_list_response = query_dynamodb(vocab_list['list_id'], todays_date, from_date)
        # print('word list response', word_list_response)

        for word_item in word_list_response:
            formatted_word=format_review_word(word_item)
            review_words[vocab_list['list_id']].append(asdict(formatted_word))

    return review_words

def query_dynamodb(list_id, todays_date, from_date):

    try:
        response = table.query(
            KeyConditionExpression=Key('PK').eq("LIST#" + list_id) & Key('SK').between("DATESENT#" + str(from_date),"DATESENT#" + str(todays_date))
        )
    except Exception as e:
        print(e.response['Error']['Message'])
        raise e
    # else:
        print("dynamo query response: ", json.dumps(response['Items'], indent=4))
    
    return response['Items']

def format_review_word(word_item):
    # print('word item: ', word_item)

    word = format_word_body(word_item['Word'])

    review_word = ReviewWord(
        list_id = word_item['PK'].split('#')[1],
        date_sent = word_item['SK'].split('#')[1],
        word = word
    )
    return review_word

def format_word_body(word):
    # print('word: ', word)

    # .get() throughout: user-created lists will not carry every field an HSK word has
    # (no HSK level, no audio until the pipeline runs, traditional only if supplied or
    # derived), and a missing attribute must not take down a read path
    word = Word(
        word_id = word.get('Word id', ''),
        simplified = word.get('Simplified', ''),
        traditional = word.get('Traditional', '') or word.get('Simplified', ''),
        pinyin = word.get('Pinyin', ''),
        definition = word.get('Definition', ''),
        audio_file_key = word.get('Audio file key', ''),
        difficulty_level = word.get('Difficulty level', ''),
        hsk_level = word.get('HSK Level', '')
    )
    return word

def format_date(date_object):

  formatted_date = date_object.strftime('%Y-%m-%d')

  return formatted_date