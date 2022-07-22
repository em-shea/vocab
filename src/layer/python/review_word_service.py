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

all_lists = vocab_list_service.get_vocab_lists()

def get_review_words(list_id, date_range):

    todays_date = format_date(datetime.today())

    filtered_lists = [l for l in all_lists if (list_id is None or l['list_id'] == list_id)]
    
    from_date = format_date(datetime.today() - timedelta(days=int(7)))
    if date_range is not None:
        from_date = format_date(datetime.today() - timedelta(days=int(date_range)))

    review_words = defaultdict(list)
    for vocab_list in filtered_lists:
        word_list_response = query_dynamodb(vocab_list['list_id'], todays_date, from_date)
        # print('word list response', word_list_response)

        for word in word_list_response:
            formatted_word=format_review_word(word)
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
        # print("dynamo query response: ", json.dumps(response['Items'], indent=4))
    
    return response['Items']

def format_review_word(query_response_word):
    # print('query response word', query_response_word)
    word_body = Word(
        word_id = query_response_word['Word']['Word id'],
        simplified = query_response_word['Word']['Simplified'],
        traditional = query_response_word['Word']['Traditional'],
        pinyin = query_response_word['Word']['Pinyin'],
        definition = query_response_word['Word']['Definition'],
        audio_file_key = query_response_word['Word']['Audio file key'],
        difficulty_level = query_response_word['Word']['Difficulty level'],
        hsk_level = query_response_word['Word']['HSK Level']
    )

    review_word = ReviewWord(
        list_id = query_response_word['PK'].split('#')[1],
        date_sent = query_response_word['SK'].split('#')[1],
        word = word_body
    )

    return review_word

def format_date(date_object):

  formatted_date = date_object.strftime('%Y-%m-%d')

  return formatted_date