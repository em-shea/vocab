import os
import json
import boto3
from boto3.dynamodb.conditions import Key

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Create or update daily practice sentences
def lambda_handler(event, context):
    print(event)
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    print('user id, ',cognito_id)

    error_message = {
        'statusCode': 502,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : false}'
    }

    try:
        sentences_response = pull_user_sentences(cognito_id)
    except Exception as e:
        print(f"Error: Failed to get user sentences.")
        print(e)
        return error_message
    
    user_sentences = format_user_sentences(sentences_response)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(user_sentences)
    }

def pull_user_sentences(congito_id):

    user_key = "USER#" + congito_id

    response = table.query(
        KeyConditionExpression=Key('PK').eq(user_key)
        # filter by sort key SENTENCES#?
    )
    print('dynamo response ', response['Items'])
    return response['Items']

def format_user_sentences(sentences_response):

    user_sentences = { "sentences" : [] }
    for item in sentences_response:
        sentence_dict = {}

        sentence_dict['cognito_id'] = item['PK'][5:]
        sentence_dict['sentence_id'] = item['Email address']
        sentence_dict['sentence'] = item['sentence']
        sentence_dict['character_set'] = item['Character set']
        sentence_dict['date_created'] = item['Date created']

        user_sentences['sentences'].append(sentence_dict)

    return user_sentences

# output:
# {
#     "sentences":[
#         {
#             "sentence_id":"123",
#             "sentence": "我喜欢学习汉语。",
#             "date_created": "2021-06-16T23:06:48.467526"
#             "list_id": "123",
#             "character_set": "simplified"
#         },
#         {
#             "sentence_id":"234",
#             "sentence": "我喜欢写句子。",
#             "date_created": "2021-06-16T23:06:48.467526"
#             "list_id": "234",
#             "character_set": "simplified"
#         }
#     ]   
# }

# dynamodb response:
#         Item = {
#                 'PK': "USER#" + body['cognito_id'],
#                 'SK': "SENTENCE#" + body['sentence_id'],
#                 'Date created': date,
#                 'List id': body['list_id'],
#                 'Character set': body['character_set'],
#                 'GSI1PK': "DATE#" + date,
#                 'GSI1SK': "USER#" + "SENTENCE#" + body['sentence_id']
#             }