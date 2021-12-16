import io
import os
import boto3
from boto3.dynamodb.conditions import Key

import sys
sys.path.append('../tests/')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Returns all of the words (and details) associated with a given list
def get_words_in_list(list_id):

    try:
        query_response = query_dynamodb(list_id)
    except Exception as e:
        print(f"Error: DyanmoDB query for word list failed.")
        print(e)
        return {
            f"error_message": "Failed to query DynamoDB. Error: {e}"
        }
    word_list = format_word_list(query_response)

    return word_list

def query_dynamodb(list_id):

    query_response = table.query(
        KeyConditionExpression=Key('PK').eq("LIST#" + list_id) & Key('SK').begins_with('WORD#') 
    )
    print('dynamo response ', query_response['Items'])

    return query_response

def format_word_list(query_response):
    word_list = []

    for item in query_response['Items']:
        if item['Word']['Audio file key'] != "":
            word_list.append(
                {
                    "list_id": item['PK'],
                    "word_id": item['SK'],
                    "word": item['Word']
                }
            )
    return word_list
