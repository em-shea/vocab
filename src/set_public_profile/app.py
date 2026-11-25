import os
import json
import boto3

import api_response
import public_profile_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])


# POST /public_profile {"public": true|false}: switch the signed-in user's public
# profile and leaderboard entry on or off. Writes only 'Public profile' and
# 'Public handle' on the user item and the user's own PUBLIC#<handle> pointer.
def lambda_handler(event, context):
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    try:
        body = json.loads(event.get('body') or '{}')
    except ValueError:
        return api_response.response(400, "Body must be JSON.")
    if not isinstance(body.get('public'), bool):
        return api_response.response(400, "'public' must be true or false.")
    try:
        result = public_profile_service.set_public(table, cognito_id, body['public'])
    except LookupError:
        return api_response.response(404, "User not found.")
    except Exception as e:
        print(f"Error: failed to set public profile for {cognito_id}")
        print(e)
        return api_response.response(502, "Failed to update public profile.")
    return api_response.response(200, "Public profile updated.", result)
