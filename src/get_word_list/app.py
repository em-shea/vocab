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
            'statusCode': 502,
            'headers': {
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Origin': '*',
            },
            'body': '{"success" : false}'
        }

    word_list = parse_response(query_response)
    print(word_list)
    # issue with words in UTF8?

    # return {
    #     'statusCode': 200,
    #     'headers': {
    #         'Access-Control-Allow-Methods': 'GET,OPTIONS',
    #         'Access-Control-Allow-Origin': '*',
    #     },
    #     'body': json.dumps(word_list)
    # }
    return word_list

def query_dynamodb(list_id):

    query_response = table.query(
        KeyConditionExpression=Key('PK').eq("LIST#" + list_id) & Key('SK').begins_with('WORD#') 
    )
    # print('dynamo response ', query_response['Items'])

    return query_response

def parse_response(query_response):

    word_list = []

    for item in query_response['Items']:
        word_list.append(
            {
                "list_id": item['PK'][5:],
                "word_id": item['SK'][5:],
                "text": item['Word']['Simplified']
            }
        )

    return word_list