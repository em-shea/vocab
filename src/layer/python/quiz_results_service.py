import os
import json
import boto3
from dataclasses import asdict
from models import Quiz
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta

import dynamodb_service

import sys
sys.path.append('../tests/')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

def retrieve_quiz_results(cognito_id, date_range):

    query_response = query_dynamodb(cognito_id, date_range)
    print(query_response)

    quiz_results = []
    for item in query_response:
        quiz_results.append(asdict(format_quiz_results(item)))
    
    return quiz_results

def query_dynamodb(cognito_id, date_range):

    # Query for all of the quizzes saved after a given date
    from_date = datetime.today() - timedelta(days=date_range)

    # set_quiz_results writes SK as 'DATE#<date>#QUIZ#<id>', so begins_with('QUIZ#')
    # could never match. The date is in the key, so range over it directly rather
    # than filtering on the 'Date created' attribute - the old filter also compared
    # a '%Y-%m-%d' string against an isoformat one, which excluded the boundary day.
    from_key = 'DATE#' + from_date.strftime('%Y-%m-%d')
    to_key = 'DATE#' + datetime.today().strftime('%Y-%m-%d') + '#￿'

    items = dynamodb_service.query_all_pages(
        table,
        KeyConditionExpression=Key('PK').eq('USER#' + cognito_id) & Key('SK').between(from_key, to_key)
    )

    # Sentences share this key range, so they have to be filtered out - but NOT with a
    # DynamoDB FilterExpression. SK is the table's range key, and a filter may only
    # reference non-key attributes:
    #   ValidationException: Filter Expression can only contain non-primary key
    #   attributes: Primary key attribute: SK
    # moto does not enforce that rule, so this only fails against real DynamoDB.
    return [item for item in items if '#QUIZ#' in item['SK']]

def format_quiz_results(quiz_results_item):

    formatted_quiz_results_item = Quiz(
        # Read the stored id rather than slicing the key - the slice assumed an
        # old 'QUIZ#<id>' shape and returns '<date>#QUIZ#<id>' for real items
        quiz_id = quiz_results_item.get('Quiz id', ''),
        date_created = quiz_results_item.get('Date created', ''),
        list_id = quiz_results_item.get('List id', ''),
        character_set = quiz_results_item.get('Character set', ''),
        question_quantity = int(quiz_results_item.get('Question quantity', 0)),
        correct_answers = int(quiz_results_item.get('Correct answers', 0)),
        quiz_data = quiz_results_item.get('Quiz data', [])
    )

    return formatted_quiz_results_item