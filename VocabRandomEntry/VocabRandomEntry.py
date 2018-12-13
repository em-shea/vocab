from botocore.vendored import requests
from random import randint
import json

def random_entry(any_list):
    """Pulls random entry from a list argument given to it"""
    random_number = randint(0,len(any_list)-1)
    random_selection = any_list[random_number]

    return random_selection

def lambda_handler(event, context):
    """Pulls data file from S3 bucket provided as an env var and passes list to random_entry function"""
    response = requests.get(event['S3BucketName'])
    imported_list = json.loads(response.text)
    word = random_entry(imported_list)

    return {
        'statusCode': 200,
        'body': word
}
