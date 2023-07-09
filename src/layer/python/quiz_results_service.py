import os
import json
import boto3
from dataclasses import asdict
from models import QuizResults
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta

import sys
sys.path.append('../tests/')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

def retrieve_quiz_results(cognito_id, date_range):

    query_response = query_dynamodb(cognito_id, date_range)
    print(query_response)

    quiz_results = []
    for item in query_response:
        quiz_results.append(asdict(_format_quiz_results(item)))
    
    return quiz_results

def query_dynamodb(cognito_id, date_range):

    # Query for all of the quizzes saved after a given date
    from_date = datetime.today() - timedelta(days=date_range)
    print(from_date)

    response = table.query(
        KeyConditionExpression=Key('PK').eq('USER#' + cognito_id) & Key('SK').begins_with('QUIZ#'),
        FilterExpression='#d >= :val',
        ExpressionAttributeNames={
            '#d': 'Date created'
        },
        ExpressionAttributeValues={
            ':val': from_date.isoformat()
        }
    )

    return response['Items']

def _format_quiz_results(quiz_results_item):

    formatted_quiz_results_item = QuizResults(
        quiz_id = quiz_results_item['SK'][5:],
        date_created = quiz_results_item['Date created'],
        list_id = quiz_results_item['List id'], 
        character_set = quiz_results_item['Character set'], 
        question_quantity = int(quiz_results_item['Question quantity']), 
        correct_answers = int(quiz_results_item['Correct answers']),
        quiz_data = quiz_results_item['Quiz data']
    )

    return formatted_quiz_results_item