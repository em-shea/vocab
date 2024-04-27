import os
import json
import boto3
import datetime

import api_response
import ksuid_service

# Add sentence_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Create or update daily practice sentences
def lambda_handler(event, context):
    print('event: ', event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    body = json.loads(event["body"])

    # Simple date format so that only one sentence is saved per day
    # date = str(datetime.datetime.now().isoformat())
    date = datetime.datetime.now().strftime('%Y-%m-%d')

    if "sentence_id" == "" or "sentence_id" == None:
        print('sentence ID empty, generating ID')
        body["sentence_id"] = generate_sentence_id()
        print('sentence_id generated: ', body["sentence_id"])

    try:
        print("updating sentence... body: ", body)
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
                'SK': "DATE#" + date + "SENTENCE#" + body['sentence_id'],
                'Sentence': body['sentence'],
                'Date created': date,
                'List id': body['list_id'],
                'Character set': body['character_set'],
                'Word': body['word'],
                'GSI1PK': "DATE#" + date,
                'GSI1SK': "SENTENCE#" + body['sentence_id']
            }
        )
    return response