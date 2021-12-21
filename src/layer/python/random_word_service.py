import io
import os
import csv
import boto3
from random import randint

import sys
sys.path.append('../tests/')

# Memoizing vocab lists variable to only load once if function is warm
vocab_lists = None

# Receives HSK level as input, returns random word
def select_random_word(hsk_level):

    # Validate hsk_level
    try:
        1 <= int(hsk_level) <= 6
    except Exception as e:
        print(e)
        return "Invalid HSK level. HSK level should be a string representing an integer between 1 and 6."

    # Only generate vocab list if the global variable is not yet assigned
    global vocab_lists

    if vocab_lists is None:
        csv_file_contents = get_s3_file()
        vocab_lists = get_vocab_lists(csv_file_contents)

    index_hsk_level = int(hsk_level) - 1

    # Gets a random entry from the vocab list
    word = random_entry(vocab_lists[index_hsk_level])

    return word

def get_s3_file():

    s3 = boto3.client('s3')

    s3_file = s3.get_object(Bucket=os.environ['WORDS_BUCKET_NAME'], Key=os.environ['WORDS_BUCKET_KEY'])
    s3_file_contents = s3_file['Body']

    return s3_file_contents.read().decode('utf-8')

def get_vocab_lists(csv_file_contents):

    stream = io.StringIO(csv_file_contents)
    reader = csv.DictReader(stream)

    # Create an empty list of lists that will hold the vocab words for each level
    local_vocab_lists = [
        [],
        [],
        [],
        [],
        [],
        [],
    ]

    for row in reader: 

        # Populates each level list with vocab of that level
        hsk_level = row['HSK Level']
        index_hsk_level = int(hsk_level) - 1
        local_vocab_lists[index_hsk_level].append(dict(row))
        
    return local_vocab_lists

# Select random entry from provided list
def random_entry(any_list):

    random_number = randint(0,len(any_list)-1)
    random_selection = any_list[random_number]

    return random_selection
