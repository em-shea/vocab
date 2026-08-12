import os
import json
import boto3
from boto3.dynamodb.conditions import Key

import api_response

# Add sentence_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Create or update daily practice sentences
def lambda_handler(event, context):
    print(event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']

    try:
        sentences_response = pull_user_sentences(cognito_id)
    except Exception as e:
        print(f"Error: Failed to get user sentences.")
        print(e)
        return api_response.response(502, "Failed to retrieve user sentences.")
    
    user_sentences = format_user_sentences(sentences_response)

    return api_response.response(200, "Successfully retrieved user sentences.", user_sentences)

def pull_user_sentences(congito_id):

    user_key = "USER#" + congito_id

    # set_sentence writes SK as 'DATE#<date>#SENTENCE#<id>', so the sentence marker is
    # in the middle of the key - begins_with('SENTENCE') could never match. Query the
    # date range and filter the quizzes back out.
    response = table.query(
        KeyConditionExpression=Key('PK').eq(user_key) & Key('SK').begins_with('DATE#')
    )

    # Filtered here rather than with a DynamoDB FilterExpression: SK is the table's
    # range key, and a filter may only reference non-key attributes:
    #   ValidationException: Filter Expression can only contain non-primary key
    #   attributes: Primary key attribute: SK
    # moto does not enforce that rule, so this only fails against real DynamoDB.
    items = [item for item in response['Items'] if '#SENTENCE#' in item['SK']]
    print('dynamo response ', items)
    return items

def format_user_sentences(sentences_response):

    user_sentences = { "sentences" : [] }
    for item in sentences_response:
        sentence_dict = {}

        # sentence_dict['cognito_id'] = item['PK'][5:]
        # Read the stored id rather than slicing the key - the slice assumed the old
        # 'SENTENCE#<id>' key shape and returns garbage for 'DATE#<date>#SENTENCE#<id>'
        sentence_dict['sentence_id'] = item['Sentence id']
        sentence_dict['sentence'] = item['Sentence']
        sentence_dict['character_set'] = item['Character set']
        sentence_dict['date_created'] = item['Date created']

        user_sentences['sentences'].append(sentence_dict)

    return user_sentences