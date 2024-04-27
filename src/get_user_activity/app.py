import json
import user_service
import review_word_service
from dataclasses import asdict

# For a given user (requires sign-in), return their metadata, subscribed lists, and the past two weeks of quizzes and sentences
def lambda_handler(event, context):
    # print('event', event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    print('user id',cognito_id)
    date_range = 10
    
    user_data = user_service.get_single_user_with_activity(cognito_id, date_range)
    print('user activity: ', user_data)
    
    # Add recent words for subscribed lists

    # for list in user_data['subscriptions']:
    #    review_word_service.get_review_words(list['list_id'], date_range)
        # append

    # print('user: ', user)

    # subscribed_lists = []

    # # Only return subscribed lists
    # for subscription in user.subscriptions:
    #     if subscription.status == "subscribed":
    #         subscribed_lists.append(subscription)

    # user.subscriptions = subscribed_lists

    print('user: ', user_data)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(asdict(user_data))
    }