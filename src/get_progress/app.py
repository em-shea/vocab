import os
import boto3

import api_response
import user_service
import vocab_list_service
import progress_service
import streak_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])


# GET /progress: for each of the signed-in user's lists, how many words it has,
# how many the user has been sent, and how many they are proficient in (rule in
# progress_service.PROFICIENT), and the daily streak (streak_service). Read-only.
def lambda_handler(event, context):
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    try:
        user = user_service.get_single_user(cognito_id)
        items = progress_service.activity_items(table, cognito_id)
        rows = progress_service.get_progress(table, cognito_id, user.subscriptions or [], items)
        streak = streak_service.get_streak(items)
        names = {l['list_id']: l.get('list_name', '') for l in vocab_list_service.get_vocab_lists_for_user(cognito_id)}
    except Exception as e:
        print(f"Error: failed to work out progress for {cognito_id}")
        print(e)
        return api_response.response(502, "Failed to retrieve progress.")

    for row in rows:
        row['list_name'] = names.get(row['list_id'], '')
    return api_response.response(200, "Successfully retrieved progress.", {
        "lists": rows,
        "proficient_rule": progress_service.PROFICIENT,
        "streak": streak,
    })
