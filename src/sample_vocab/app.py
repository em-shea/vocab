import json
from random import randint

import list_word_service
import vocab_list_service

# Selects 5 random entries from each level
def lambda_handler(event, context):

    # Create an empty dictionary that will hold the 5 words for each level
    sample_words_response = {}

    all_lists = vocab_list_service.get_vocab_lists()

    for list in all_lists:
        sample_words_response[list['list_id']] = []
        all_words = list_word_service.get_words_in_list(list['list_id'])
        for i in range(5):
            sample_words_response[list['list_id']].append(select_random_word(all_words))

    # print('sample words: ', sample_words_response)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            # 'Access-Control-Allow-Origin': os.environ['DomainName'],
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(sample_words_response)
    } 

def select_random_word(word_list):

    random_number = randint(0,len(word_list)-1)
    random_word = word_list[random_number]
    return random_word
