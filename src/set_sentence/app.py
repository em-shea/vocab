import os
import json
import boto3
import datetime

import api_response
import ksuid_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Create or update daily practice sentences
def lambda_handler(event, context):
    print(event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    body = json.loads(event["body"])
    date = str(datetime.datetime.now().isoformat())

    if "sentence_id" == "":
        body["sentence_id"] = generate_sentence_id()

    try:
        response = update_sentence(cognito_id, body, date)
    except Exception as e:
        print(f"Error: Failed to update sentence - {body}")
        print(e)
        return api_response.response(502, f"Failed to save sentence.")

    return api_response.response(200, f"Successfully saved sentence.")

def generate_sentence_id():
    sentence_id = str(ksuid_service.generate_ksuid())
    return sentence_id

def update_sentence(cognito_id, body, date):
    response = table.put_item(
        Item = {
                'PK': "USER#" + cognito_id,
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