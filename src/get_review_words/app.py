import os
import json
import boto3
from datetime import datetime
from datetime import timedelta
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

import vocab_list_service
import review_word_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

all_lists = vocab_list_service.get_vocab_lists()

def lambda_handler(event,context):

  params = event.get('queryStringParameters') or {}
  list_id_param = params.get('list_id', None)
  date_range_param = params.get('date_range', None)

  review_words = review_word_service.get_review_words(list_id=list_id_param, date_range=date_range_param)

  return {
          'statusCode': 200,
          'headers': {
              'Access-Control-Allow-Methods': 'GET,OPTIONS',
              'Access-Control-Allow-Origin': '*',
          },
          'body': json.dumps(review_words)
        }