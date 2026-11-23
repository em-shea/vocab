import os
import json
import boto3
from datetime import datetime, timedelta, timezone

import api_response

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Like sentences: practice can be recorded for any word from the last 30 days.
MAX_DAYS_BACK = 30


# Record that a user practised writing a word's characters (digital stroke
# practice on the site). One item per user, word date, list and word: practising
# again rewrites the same item, so nothing accumulates. Adds items only; it never
# reads, changes or deletes any other item.
def lambda_handler(event, context):
    print('event: ', event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    try:
        body = json.loads(event["body"] or "{}")
    except (TypeError, ValueError):
        return api_response.response(400, "Body must be JSON.")

    missing = [key for key in ("list_id", "word_id", "characters") if not body.get(key)]
    if missing:
        return api_response.response(400, f"Missing: {', '.join(missing)}.")

    today = datetime.now(timezone.utc).date()
    try:
        date = writing_date(body.get("date"), today)
    except ValueError as e:
        return api_response.response(400, str(e))

    try:
        save_writing(cognito_id, body, date)
    except Exception as e:
        print(f"Error: Failed to save writing practice - {body}")
        print(e)
        return api_response.response(502, "Failed to save writing practice.")

    return api_response.response(200, "Successfully saved writing practice.", {"date": date})


def writing_date(value, today):
    """The date to file practice under: the word's date, as YYYY-MM-DD."""
    if value in (None, ""):
        return today.isoformat()
    try:
        date = datetime.strptime(str(value), '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Date must be YYYY-MM-DD.")
    if date > today:
        raise ValueError("Date cannot be in the future.")
    if date < today - timedelta(days=MAX_DAYS_BACK):
        raise ValueError(f"Writing can only be recorded for the last {MAX_DAYS_BACK} days.")
    return date.isoformat()


def save_writing(cognito_id, body, date):
    return table.put_item(
        Item={
            'PK': "USER#" + cognito_id,
            'SK': "DATE#" + date + "#WRITING#" + str(body['list_id']) + "#" + str(body['word_id']),
            'Date created': date,
            'Date written': datetime.now(timezone.utc).isoformat(),
            'List id': str(body['list_id']),
            'Word id': str(body['word_id']),
            'Characters': str(body['characters'])[:20],
            'Character set': body.get('character_set', ''),
        }
    )
