import json
import datetime
import user_service
import review_word_service
from dataclasses import asdict
from models import User, Subscription, Quiz, Sentence
from datetime import datetime, timedelta

# For a given user (requires sign-in), return their metadata, subscribed lists, and the past two weeks of quizzes and sentences
def lambda_handler(event, context):
    # print('event', event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    print('user id',cognito_id)
    date_range = 10
    
    user_data = user_service.get_single_user_with_activity(cognito_id, date_range)
    print('user activity: ', user_data)

    # Create array of dates since date_range
    dates = []
    for i in range(date_range):
        dates.append(datetime.today() - timedelta(days=i))
    print('dates: ', dates)

    # Query for recent words for each list the user is subscribed to
    user_recent_words = []
    for list in user_data.subscriptions:
       recent_words_for_list = review_word_service.get_review_words(list.list_id, date_range)
       print('recent words for list: ', recent_words_for_list)
       for word in recent_words_for_list[list.list_id]:
           user_recent_words.append(word)
    print('user recent words: ', user_recent_words)

    # Loop through dates, then loop through words, sentences, quizzes
    # Add words and sentence
    user_activity = {}
    for date in dates:
        user_activity[date.strftime('%Y-%m-%d')] = {}
        for word in user_recent_words:
            if word['date'] == date.strftime('%Y-%m-%d'):
                user_activity[date.strftime('%Y-%m-%d')]['word'] = word
        for sentence in user_data.sentences:
            if sentence['date'] == date.strftime('%Y-%m-%d'):
                user_activity[date.strftime('%Y-%m-%d')]['sentence'] = sentence
        for quiz in user_data.quizzes:
            if quiz['date'] == date.strftime('%Y-%m-%d'):
                user_activity[date.strftime('%Y-%m-%d')]['quiz'] = quiz
    print('user activity: ', user_activity)
    
    user_data_dict = asdict(user_data)
    print('user data dict: ', user_data_dict)
    user_data_dict['activity'] = user_activity
    # Remove quizzes and sentences from user_data_dict
    user_data_dict.pop('quizzes')
    user_data_dict.pop('sentences')
    print('user data dict without quiz, sentences: ', user_data_dict)

    print('user: ', user_data)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(asdict(user_data))
    }