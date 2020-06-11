import io
import os
import csv
import boto3
from random import randint

# Memoizing vocab lists variable to only load once if function is warm
vocab_lists = None

# Receives HSK level as input, returns random word
def select_random_word(hsk_level):

    global vocab_lists
    
    # Only generate vocab list if the global variable is not yet assigned
    if vocab_lists is None:
        vocab_lists = get_vocab_lists()

    index_hsk_level = int(hsk_level) - 1

    # Gets a random entry from the vocab list
    word = random_entry(vocab_lists[index_hsk_level])

    return word

def get_vocab_lists():

    s3 = boto3.client('s3')

    # Read file from S3
    csv_file = s3.get_object(Bucket=os.environ['WORDS_BUCKET_NAME'], Key=os.environ['WORDS_BUCKET_KEY'])
    csv_response = csv_file['Body'].read()
    stream = io.StringIO(csv_response.decode("utf-8"))
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
