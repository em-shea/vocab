import os
import json
from datetime import datetime, timezone

import boto3

import api_response

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Sign-ups close at the end of this day, UTC (Emily, 2026-11-26).
CLOSES = '2026-12-31'
MAX_ANSWER = 500


def is_open(now=None):
    now = now or datetime.now(timezone.utc)
    return now.date().isoformat() <= CLOSES


# POST /testers {"answer": "..."} (answer optional): the signed-in user joins the
# early testers, which gives them the Early Tester badge. Writes only
# 'Founding tester' (the badge's stored flag; the name predates "Early Tester"),
# 'Tester since' (set once) and, if given, 'Tester answer' on the user's own
# item. Never creates a user.
def lambda_handler(event, context, now=None):
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    now = now or datetime.now(timezone.utc)
    if not is_open(now):
        return api_response.response(403, "Early tester sign-ups have closed.")
    try:
        body = json.loads(event.get('body') or '{}')
    except ValueError:
        return api_response.response(400, "Body must be JSON.")
    answer = body.get('answer')
    if answer is not None and not isinstance(answer, str):
        return api_response.response(400, "'answer' must be text.")
    answer = (answer or '').strip()[:MAX_ANSWER]

    names = {'#t': 'Founding tester', '#s': 'Tester since'}
    values = {':t': True, ':s': now.isoformat()}
    expression = 'SET #t = :t, #s = if_not_exists(#s, :s)'
    if answer:
        names['#a'] = 'Tester answer'
        values[':a'] = answer
        expression += ', #a = :a'
    key = 'USER#' + cognito_id
    try:
        result = table.update_item(
            Key={'PK': key, 'SK': key},
            UpdateExpression=expression,
            ConditionExpression='attribute_exists(PK)',
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues='ALL_NEW',
        )
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return api_response.response(404, "User not found.")
    except Exception as e:
        print(f"Error: failed to add early tester {cognito_id}")
        print(e)
        return api_response.response(502, "Failed to join.")
    return api_response.response(200, "Joined the early testers.", {
        'tester': True, 'since': result['Attributes'].get('Tester since'), 'closes': CLOSES,
    })
