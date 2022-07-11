import os
import json
import boto3
import datetime
from boto3.dynamodb.conditions import Key

import api_response
import ksuid_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Put a quiz results record
def lambda_handler(event, context):
    print(event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    body = json.loads(event["body"])
    date = str(datetime.datetime.now().isoformat())

    body["quiz_id"] = generate_quiz_id()

    # Add max quiz results records a user can save for a given day?
    try:
        response = put_quiz_result(cognito_id, body, date)
        print(response)
    except Exception as e:
        print(f"Error: Failed to put quiz result - {body}")
        print(e)
        return api_response.response(502, f"Failed to put quiz results record.")

    return api_response.response(200, f"Successfully put quiz results record.")

def generate_quiz_id():
    quiz_id = str(ksuid_service.generate_ksuid())
    return quiz_id

def put_quiz_result(cognito_id, body, date):

    response = table.put_item(
        Item = {
                'PK': "USER#" + cognito_id,
                'SK': "QUIZ#" + body['quiz_id'],
                'Quiz data': body['quiz-data'],
                'Date created': date,
                'List id': body['list_id'],
                'Character set': body['character_set'],
                'Question set type': body['question_set_type'],
                'Question quantity': body['question_quantity'],
                'Percentage correct': body['percentage_correct'],
                'GSI1PK': "DATE#" + date,
                'GSI1SK': "USER#" + "QUIZ#" + body['quiz_id']
            }
        )
    return response