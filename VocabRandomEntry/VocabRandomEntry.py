import json
import io
import csv
import os
import boto3
from botocore.vendored import requests
from random import randint

s3 = boto3.client('s3')

def random_entry(any_list):
    """Pulls random entry from a list argument given to it"""
    random_number = randint(0,len(any_list)-1)
    random_selection = any_list[random_number]

    return random_selection

def lambda_handler(event, context):
    """Pulls a random vocabulary word from S3"""
    # Pulls data file from S3 bucket provided as an env var"""
    print(event)
    print(event["hsk_level"])
    hsk_level = event["hsk_level"]

    csv_file = s3.get_object(Bucket=os.environ['S3_BUCKET_NAME'], Key=os.environ['S3_BUCKET_KEY'])
    csv_response = csv_file['Body'].read()
    stream = io.StringIO(csv_response.decode("utf-8"))
    
    # Reads and prints the CSV file as a list of dictionaries
    filter_level = {hsk_level: 1}
    with open('data.tsv', 'r') as f_name:
        for line in csv.DictReader(stream, delimiter='\t'):
            if line['HSK Level'] not in filter_countries:
                print(line)
    

    reader = csv.DictReader(stream)
    vocab_list = []
    for row in reader:
        vocab_list.append(dict(row))
    print(vocab_list)


    # Calls the random_entry function on the list
    word = random_entry(vocab_list)

    return {
        'statusCode': 200,
        'body': word
}