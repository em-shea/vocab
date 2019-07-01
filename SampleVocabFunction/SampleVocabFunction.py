import json
import io
import csv
import os
import boto3
import random
from botocore.vendored import requests

s3 = boto3.client('s3')

# Pull data from given S3 file and select 5 random entries from each level
def lambda_handler(event, context):

    # Pulls data file from S3 bucket provided as an env var
    csv_file = s3.get_object(Bucket=os.environ['S3_BUCKET_NAME'], Key=os.environ['S3_BUCKET_KEY'])
    csv_response = csv_file['Body'].read()
    stream = io.StringIO(csv_response.decode("utf-8"))
    
    reader = csv.DictReader(stream)
    
    # Create an empty list of lists that will hold the vocab words for each level
    vocab_lists = [
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
        vocab_lists[index_hsk_level].append(dict(row))

    # Create an empty dictionary that will hold the 5 words for each level
    complete_response = {}

    # For each level list, create a key in the response dict and set the value to a list of 5 sample words
    for vocab_list in vocab_lists:
        hsk_level = vocab_list[0]['HSK Level']
        complete_response[hsk_level] = random.sample(vocab_list, 5)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            # 'Access-Control-Allow-Origin': os.environ['DomainName'],
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(complete_response)
    }