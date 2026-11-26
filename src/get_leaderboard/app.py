import os
import boto3

import api_response
import public_profile_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])


# GET /leaderboard: no sign-in. This week's ranking of public profiles only
# (rules in public_profile_service.get_leaderboard). Read-only.
def lambda_handler(event, context):
    try:
        board = public_profile_service.get_leaderboard(table)
    except Exception as e:
        print("Error: failed to build leaderboard")
        print(e)
        return api_response.response(502, "Failed to retrieve leaderboard.")
    return api_response.response(200, "Successfully retrieved leaderboard.", board)
