import json
import io
import csv
import os

import sys
sys.path.insert(0, '/opt')
from vocab_random_word import select_random_word

# Selects 5 random entries from each level
def lambda_handler(event, context):

    # Create an empty dictionary that will hold the 5 words for each level
    complete_response = {}

    # Loop through all 6 levels
    for hsk_level in range(1, 7):
        
        # Create a key in the response dict and set the value to an empty list
        complete_response[hsk_level] = []
        
        # Loop through 5 times generating 5 sample words and appending for the given level list
        for sample_words in range(5):
            sample_word = select_random_word(hsk_level)
            complete_response[hsk_level].append(sample_word)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            # 'Access-Control-Allow-Origin': os.environ['DomainName'],
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(complete_response)
    }