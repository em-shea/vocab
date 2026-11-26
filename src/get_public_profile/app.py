import os
import boto3

import api_response
import public_profile_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])


# GET /public_profile?handle=<handle>: no sign-in. Only profiles their owner has
# made public; anything else is a 404, so a handle can't be probed. Read-only.
def lambda_handler(event, context):
    handle = ((event.get('queryStringParameters') or {}).get('handle') or '').strip().lower()
    try:
        profile = public_profile_service.get_public_profile(table, handle)
    except Exception as e:
        print(f"Error: failed to read public profile {handle!r}")
        print(e)
        return api_response.response(502, "Failed to retrieve profile.")
    if not profile:
        return api_response.response(404, "Profile not found.")
    return api_response.response(200, "Successfully retrieved profile.", profile)
