import os
import json
import boto3
from boto3.dynamodb.conditions import Key

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Given a list id, retrieve an array of word ids and characters within that list
# Triggered by state machine to generate pronunciation audio files for a given list

def lambda_handler(event, context):
    # print('event', event)
    list_id = event['listId']

    try:
        query_response = query_dynamodb(list_id)
    except Exception as e:
        print(f"Error: DyanmoDB query for word list failed.")
        print(e)
        return {
            f"error_message": "Failed to query DynamoDB. Error: {e}"
        }

    word_list = parse_response(query_response)
    response_body = {
        "word_list": word_list
    }

    print(response_body)

    return response_body

def query_dynamodb(list_id):

    query_response = table.query(
        KeyConditionExpression=Key('PK').eq("LIST#" + list_id) & Key('SK').begins_with('WORD#') 
    )
    # print('dynamo response ', query_response['Items'])

    return query_response

def parse_response(query_response):

    word_list = []

    for item in query_response['Items']:
        if item['Audio file key'] != "":
            word_list.append(
                {
                    "list_id": item['PK'],
                    "word_id": item['SK'],
                    "text": item['Word']['Simplified']
                }
            )

    return word_list