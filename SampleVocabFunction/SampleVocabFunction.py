import json
import io
import csv
import os
import boto3
import random
from botocore.vendored import requests

s3 = boto3.client('s3')

# def random_entry(any_list):
#     """Pulls random entry from a list argument given to it"""
#     random_number = randint(0,len(any_list)-1)
#     random_selection = any_list[random_number]

#     return random_selection

def lambda_handler(event, context):

    """Pulls a random vocabulary word from S3"""
    # Pulls data file from S3 bucket provided as an env var"""

    csv_file = s3.get_object(Bucket=os.environ['S3_BUCKET_NAME'], Key=os.environ['S3_BUCKET_KEY'])
    csv_response = csv_file['Body'].read()
    stream = io.StringIO(csv_response.decode("utf-8"))
    
    # Reads and prints the CSV file as a list of dictionaries
    reader = csv.DictReader(stream)
    vocab_lists = [
        [],
        [],
        [],
        [],
        [],
        [],
    ]

    for row in reader: 
        
        hsk_level = row['HSK Level']
        index_hsk_level = int(hsk_level) - 1
        vocab_lists[index_hsk_level].append(dict(row))

    # Default dict example
    complete_response = {}
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
        'body': json.dumps(words)
    }