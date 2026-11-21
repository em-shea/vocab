import os
import json
import boto3
from datetime import datetime, timedelta, timezone

import api_response
import ksuid_service

# Add sentence_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# How far back a sentence may be written. The site offers the last 10 days of
# words (get_user_activity's window); 30 leaves room to widen that without a
# backend change.
MAX_DAYS_BACK = 30

# Create or update daily practice sentences
def lambda_handler(event, context):
    print('event: ', event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    body = json.loads(event["body"])

    # A sentence is filed under the date its word was sent, so get_user_activity
    # can pair it with that word (it matches on date and word id). The site sends
    # that date as "date"; without one (older clients), it is today, as before.
    today = datetime.now(timezone.utc).date()
    try:
        date = sentence_date(body.get("date"), today)
    except ValueError as e:
        return api_response.response(400, str(e))

    if body["sentence_id"] == "":
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

    # The id is returned so a client that sent none can update the same sentence later.
    return api_response.response(200, f"Successfully saved sentence.", {"sentence_id": body["sentence_id"], "date": date})

def sentence_date(value, today):
    """The date to file a sentence under: the word's date, as YYYY-MM-DD."""
    if value in (None, ""):
        return today.isoformat()
    try:
        date = datetime.strptime(str(value), '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Date must be YYYY-MM-DD.")
    if date > today:
        raise ValueError("Date cannot be in the future.")
    if date < today - timedelta(days=MAX_DAYS_BACK):
        raise ValueError(f"Sentences can only be written for the last {MAX_DAYS_BACK} days.")
    return date.isoformat()

def generate_sentence_id():
    sentence_id = str(ksuid_service.generate_ksuid())
    return sentence_id

def update_sentence(cognito_id, body, date):
    response = table.put_item(
        Item = {
                'PK': "USER#" + cognito_id,
                'SK': "DATE#" + date + "#SENTENCE#" + body['sentence_id'],
                'Sentence': body['sentence'],
                'Sentence id': body['sentence_id'],
                'Date created': date,
                # When it was actually written, which can be later than the word's date.
                'Date written': datetime.now(timezone.utc).isoformat(),
                'List id': body['list_id'],
                'Character set': body['character_set'],
                'Word': body['word'],
                'GSI1PK': "DATE#" + date,
                'GSI1SK': "SENTENCE#" + body['sentence_id']
            }
        )
    return response