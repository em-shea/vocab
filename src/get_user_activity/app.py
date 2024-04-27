import json
from dataclasses import asdict

import user_activity_service

# For a given user (requires sign-in), return their metadata, subscribed lists, and the past two weeks of quizzes and sentences
def lambda_handler(event, context):
    # print('event', event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    print('user id',cognito_id)
    
    user = user_activity_service.get_user_activity(cognito_id)

    # print('user: ', user)

    # subscribed_lists = []

    # # Only return subscribed lists
    # for subscription in user.subscriptions:
    #     if subscription.status == "subscribed":
    #         subscribed_lists.append(subscription)

    # user.subscriptions = subscribed_lists

    print('user: ', user)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(asdict(user))
    }