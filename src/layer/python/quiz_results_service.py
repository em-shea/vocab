import os
import json
import boto3
import datetime
from models import QuizResults

import sys
sys.path.append('../tests/')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

def retrieve_quiz_results(cognito_id, date_range):

    todays_date = str(datetime.datetime.now().isoformat())

    query_response = query_dynamodb(cognito_id, todays_date, date_range)
    print(query_response)

    quiz_results = {}
    for item in query_response:
        _format_quiz_results(item).append(quiz_results)
    
    return quiz_results

def query_dynamodb(cognito_id, todays_date, date_range):

    # Convert precise datetime to simple date
    simple_date = todays_date

    # Retrieves single day, how to filter for dates between range?
    response = table.query(
        KeyConditionExpression=Key('PK').eq('USER#' + cognito_id) & Key('SK').begins_with('QUIZ#'),
        FilterExpression='#d = :val',
        ExpressionAttributeNames={
            '#d': 'Date created'
        },
        ExpressionAttributeValues={
            ':val': simple_date
        }
    )

    return response['Items']

def _format_quiz_results(quiz_results_item):

    formatted_quiz_results_item = QuizResults(
        quiz_id = quiz_results_item['SK'][5:],
        date_created = quiz_results_item['Date created'],
        list_id = quiz_results_item['List id'], 
        character_set = quiz_results_item['Character set'], 
        question_set_type = quiz_results_item['Question set type'], 
        question_quantity = quiz_results_item['Question quantity'], 
        percentage_correct = quiz_results_item['Percentage correct'], 
        quiz_data = quiz_results_item['Quiz data']
    )

    return formatted_quiz_results_item