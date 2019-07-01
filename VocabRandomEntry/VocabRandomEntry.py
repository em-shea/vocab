import json
import io
import csv
import os
import boto3
from botocore.vendored import requests
from random import randint

s3 = boto3.client('s3')

def lambda_handler(event, context):

    hsk_level = event["hsk_level"]

    # Reads file from S3
    csv_file = s3.get_object(Bucket=os.environ['S3_BUCKET_NAME'], Key=os.environ['S3_BUCKET_KEY'])
    csv_response = csv_file['Body'].read()
    stream = io.StringIO(csv_response.decode("utf-8"))
    
    # Reads and prints the CSV file as a list of dictionaries
    reader = csv.DictReader(stream)
    vocab_list = []
    for row in reader:
        if row['HSK Level'] == hsk_level:
            vocab_list.append(dict(row))
    print(vocab_list)

    # Gets a random entry from the vocab list
    word = random_entry(vocab_list)

    return {
        'statusCode': 200,
        'body': word
}

# Select random entry from provided list
def random_entry(any_list):

    random_number = randint(0,len(any_list)-1)
    random_selection = any_list[random_number]

    return random_selection