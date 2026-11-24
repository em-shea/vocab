import os
import json
import hashlib
import boto3
from datetime import datetime, timezone

import api_response

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# POST /push: turn daily word notifications on or off for one device.
#   {"action": "subscribe", "subscription": {endpoint, keys: {p256dh, auth}}}
#   {"action": "unsubscribe", "subscription": {"endpoint": ...}}
#
# One item per user and device (SK PUSH#<hash of the endpoint>), with GSI1PK
# "PUSH" so the daily sender can find them all. Subscribing again rewrites the
# same item. Unsubscribing deletes only that one PUSH# item of the caller's own:
# never a user, list, quiz or sentence item.
MAX_FIELD = 1024


def push_key(endpoint):
    return "PUSH#" + hashlib.sha256(endpoint.encode('utf-8')).hexdigest()[:32]


def lambda_handler(event, context):
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    try:
        body = json.loads(event.get("body") or "{}")
    except (TypeError, ValueError):
        return api_response.response(400, "Body must be JSON.")

    action = body.get("action")
    sub = body.get("subscription") or {}
    endpoint = sub.get("endpoint", "")
    if action not in ("subscribe", "unsubscribe"):
        return api_response.response(400, "Action must be subscribe or unsubscribe.")
    if not isinstance(endpoint, str) or not endpoint.startswith("https://") or len(endpoint) > MAX_FIELD:
        return api_response.response(400, "A push subscription endpoint (https) is required.")

    key = {'PK': "USER#" + cognito_id, 'SK': push_key(endpoint)}
    try:
        if action == "unsubscribe":
            table.delete_item(Key=key)
            return api_response.response(200, "Daily word notifications turned off for this device.")

        keys = sub.get("keys") or {}
        p256dh, auth = keys.get("p256dh"), keys.get("auth")
        if not all(isinstance(v, str) and 0 < len(v) <= MAX_FIELD for v in (p256dh, auth)):
            return api_response.response(400, "Subscription keys p256dh and auth are required.")
        table.put_item(Item={
            **key,
            'Endpoint': endpoint,
            'P256dh': p256dh,
            'Auth': auth,
            'Date created': datetime.now(timezone.utc).isoformat(),
            'GSI1PK': "PUSH",
            'GSI1SK': "USER#" + cognito_id + "#" + key['SK'],
        })
    except Exception as e:
        print(f"Error: failed to {action} push for {cognito_id}")
        print(e)
        return api_response.response(502, "Failed to update notifications.")
    return api_response.response(200, "Daily word notifications turned on for this device.")
