import os
import json
import boto3
import datetime

import ksuid_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['DYNAMODB_TABLE_NAME'])

# Create or update daily practice sentences
def lambda_handler(event, context):
    print(event)

    body = json.loads(event["body"])
    date = str(datetime.datetime.now().isoformat())

    error_message = {
        'statusCode': 502,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : false}'
    }

    if "sentence_id" not in body:
        body["sentence_id"] = generate_sentence_id()

    try:
        response = update_sentence(body, date)
    except Exception as e:
        print(f"Error: Failed to update sentence - {body}")
        print(e)
        return error_message

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps({"success" : True, "sentence_id" : str(body["sentence_id"]) })
    }

def generate_sentence_id():

    sentence_id = ksuid_service.generate_ksuid()

    return sentence_id

def update_sentence(body, date):

    response = table.put_item(
        Item = {
                'PK': "USER#" + body['cognito_id'],
                'SK': "SENTENCE#" + body['sentence_id'],
                'Sentence': body['sentence'],
                'Date created': date,
                'List id': body['list_id'],
                'Character set': body['character_set'],
                'GSI1PK': "DATE#" + date,
                'GSI1SK': "USER#" + "SENTENCE#" + body['sentence_id']
            }
        )
    return response