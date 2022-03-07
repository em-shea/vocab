import os
import boto3
from boto3.dynamodb.conditions import Key, Attr

import sys
sys.path.append('../tests/')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Returns all of the words (and details) associated with a given list
def get_words_in_list(list_id, limit=None, last_word_token=None, audio_file_key_check=False):

    try:
        query_response = query_dynamodb(list_id, limit=limit, last_word_token=last_word_token, audio_file_key_check=audio_file_key_check)
    except Exception as e:
        print(f"Error: DyanmoDB query for word list failed.")
        print(e)
        return {
            f"error_message": "Failed to query DynamoDB. Error: {e}"
        }
    word_list = format_word_list(query_response)

    return word_list

def query_dynamodb(list_id, limit=None, last_word_token=None, audio_file_key_check=False):

    if last_word_token is not None:
        # Start from last word processed
        key_condition = Key('PK').eq('LIST#' + list_id) & Key('SK').gt(last_word_token)
    else:
        # Start at beginning of words
        key_condition = Key('PK').eq('LIST#' + list_id) & Key('SK').begins_with('WORD#')

    query = {
        'KeyConditionExpression': key_condition
    }
    if limit is not None:
        query['Limit'] = limit
    # Decided against using a filter expression (audio_file_check set to False) since I need to set a last_word_token
    # TODO: limit/filter results with fewer DynamoDB calls and Step Functions map iterations
    if audio_file_key_check is not False:
        query['FilterExpression'] = "#w.#af = :val"
        query['ExpressionAttributeNames'] = {
            '#w': 'Word',
            '#af': 'Audio file key'
        }
        query['ExpressionAttributeValues'] = {
            ':val': ''
        }

    query_response = table.query(**query)

    return query_response

def format_word_list(query_response):
    word_list = []

    # Reformat item['Word'] contents to lower caps/underscores?
    for item in query_response['Items']:
        word_list.append(
            {
                "list_id": item['PK'],
                "word_id": item['SK'],
                "word": item['Word']
            }
        )
    return word_list
