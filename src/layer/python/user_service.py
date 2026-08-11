import os
import boto3
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
from models import User, Subscription, Quiz, Sentence
from review_word_service import format_word_body
from quiz_results_service import format_quiz_results

import dynamodb_service

import sys
sys.path.append('../tests/')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Item type prefixes for the SK of items under a USER# partition. Ordered in ASCII as
# DATE# < HERO# < LIST# < PROGRESS < USER#, which matters for the range queries below.
SK_USER_PREFIX = 'USER#'
SK_LIST_PREFIX = 'LIST#'
SK_DATE_PREFIX = 'DATE#'
SK_QUIZ_MARKER = '#QUIZ#'
SK_SENTENCE_MARKER = '#SENTENCE#'

# Upper bound for a user's items - sorts after every SK we write under USER#<sub>.
SK_UPPER_BOUND = 'USER#￿'

# Retrieves user metadata and lists
def get_single_user(cognito_id):

    user_data = query_single_user(cognito_id)
    response = _format_user_data(user_data)

    return response

def query_single_user(cognito_id):

    user_key = "USER#" + cognito_id

    # Bounded rather than gt('LIST'): the old open-ended range swept up every item type
    # sorting after 'LIST', so new SK prefixes landed here silently
    response = _query_all_pages(
        KeyConditionExpression=Key('PK').eq(user_key) & Key('SK').between(SK_LIST_PREFIX, SK_UPPER_BOUND)
    )
    # print('query_single_user dynamo response ', response)
    return response

# Retrieve user metadata, lists, and activity (quizzes, sentences)
def get_single_user_with_activity(cognito_id, date_range=10):

    user_data = query_single_user_with_activity(cognito_id, date_range)
    response = _format_user_data(user_data)

    return response

def query_single_user_with_activity(cognito_id, date_range):

    user_key = "USER#" + cognito_id

    from_date = datetime.today() - timedelta(days=int(date_range))
    query_date = 'DATE#' + from_date.strftime('%Y-%m-%d')

    # Query captures metadata, lists, and quizzes and sentences for the given date range.
    # Upper-bounded so item types added later do not silently widen this read.
    response = _query_all_pages(
        KeyConditionExpression=Key('PK').eq(user_key) & Key('SK').between(query_date, SK_UPPER_BOUND)
    )
    print('query_single_user_with_quiz_sentence_history dynamo response ', response)
    return response

def _query_all_pages(**query_kwargs):
    return dynamodb_service.query_all_pages(table, **query_kwargs)

def get_subscribed_list_ids():
    """Ids of every list with at least one active subscription.

    Lets the daily word job bound its fan-out to lists someone actually reads,
    rather than to every list that has ever been created.
    """
    items = query_all_users()

    list_ids = set()
    for item in items:
        sk = item['SK']
        if sk.startswith(SK_LIST_PREFIX) and item.get('Status') == 'subscribed':
            list_ids.add(sk.split('#')[1])

    return list_ids

def get_all_users():

    query_response = query_all_users()
    grouped_user_and_subs = group_users_and_subs(query_response)
    response = []
    for user_id, user in grouped_user_and_subs.items():
        response.append(_format_user_data(user))

    return response

def query_all_users():

    # Note that this query uses GSI1 which is already limited to metadata and lists (does not pull quizzes and sentences)
    # Paginated: this is a single partition holding every user, so it outgrows the
    # 1MB response cap. SendDailyEmail iterates whatever this returns.
    response = _query_all_pages(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq('USER')
    )
    # print(response)
    return response

def group_users_and_subs(dynamo_response):

    grouped_user_and_subs = {}
    for item in dynamo_response:
        if item['PK'] not in grouped_user_and_subs:
            grouped_user_and_subs[item['PK']] = []
        grouped_user_and_subs[item['PK']].append(item)

    # print('grouped: ', grouped_user_and_subs)
    return grouped_user_and_subs

def _format_user_data(user_data):

    user = User(
        email_address = '',
        user_id = '', 
        character_set_preference = '',
        user_alias = '', 
        user_alias_pinyin = '', 
        user_alias_emoji = '',
        subscriptions = [],
        quizzes = [],
        sentences = []
    )

    #  Loop through all users and subs
    # Dispatch is on SK *prefix*, not substring: a substring test ('USER' in SK) matches
    # any future key containing the token and routes it to the wrong branch.
    for item in user_data:
        # print(item)
        sk = item['SK']

        # If Dynamo item is user metadata, create User class
        if sk.startswith(SK_USER_PREFIX):
            print('user', item.get('Email address'))
            # .get() throughout: attributes added later (Language preference, Feature
            # flags) do not exist on records written before they were introduced
            user.email_address = item.get('Email address', '')
            user.user_id = item['PK'][5:]
            user.character_set_preference = item.get('Character set preference', 'simplified')
            user.date_created = item.get('Date created')
            user.user_alias = item.get('User alias', 'Not set')
            user.user_alias_pinyin = item.get('User alias pinyin', 'Not set')
            user.user_alias_emoji = item.get('User alias emoji', 'Not set')

        # If Dynamo item is a list subscription, add the list to the user's lists dict
        elif sk.startswith(SK_LIST_PREFIX):
            # Filter out lists that are not subscribed
            if item.get('Status') == 'subscribed':
                print('list', item.get('List name'))
                # Shortening list id from unique id (ex, LIST#1ebcad40-bb9e-6ece-a366-acde48001122#SIMPLIFIED)
                # Split rather than slice by length so the character set suffix does
                # not have to be counted by hand
                sk_parts = sk.split('#')
                list_id = sk_parts[1]

                sub = Subscription(
                    list_name = item.get('List name', ''),
                    unique_list_id = sk[5:],
                    list_id = list_id,
                    character_set = item.get('Character set', ''),
                    status = item['Status'],
                    date_subscribed = item.get('Date subscribed', '')
                )
                user.subscriptions.append(sub)

        # Quizzes and sentences both live under DATE#<date>#<TYPE>#<id>
        elif sk.startswith(SK_DATE_PREFIX) and SK_QUIZ_MARKER in sk:
            print('quiz item: ', item)
            quiz = format_quiz_results(item)
            user.quizzes.append(quiz)

        elif sk.startswith(SK_DATE_PREFIX) and SK_SENTENCE_MARKER in sk:
            print('sentence item: ', item)
            sentence = Sentence(
                sentence_id = item.get('Sentence id', ''),
                sentence = item.get('Sentence', ''),
                date_created = item.get('Date created', ''),
                list_id = item.get('List id', ''),
                character_set = item.get('Character set', ''),
                word = format_word_body(item.get('Word', {}))
            )
            user.sentences.append(sentence)

        else:
            print('Item does not match expected type - user, list, quiz, sentences. Item: ', item)
    
    # Sort lists by list id to appear in order (Level 1, Level 2, etc.)
    user.subscriptions = sorted(user.subscriptions, key=lambda k: k.list_id, reverse=False)

    print('formatted user ', user)
    return user