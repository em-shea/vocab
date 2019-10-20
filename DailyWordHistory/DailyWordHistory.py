import os
import json
import boto3
from datetime import datetime
from datetime import timedelta
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamo = boto3.resource('dynamodb')
table = dynamo.Table(os.environ['TABLE_NAME'])

all_lists = [
    'HSKLevel1',
    'HSKLevel2',
    'HSKLevel3',
    'HSKLevel4',
    'HSKLevel5',
    'HSKLevel6'
  ]

def lambda_handler(event,context):

  # Words returned from Dynamo
  items = []

  # Set today's date and dates 30 and 90 days before today's date
  todays_date = format_date(datetime.today())

  # Extract query string parameters
  # Query string parameters should be a the list name (ex, HSKLevel1) and a number of days (ex, 7)
  if 'queryStringParameters' in event and event['queryStringParameters'] is not None:

    # Set word list
    if 'list' in event['queryStringParameters']:
      list_id = event["queryStringParameters"]['list']

      # Set date range
      if 'date_range' in event["queryStringParameters"]:
        date_range = event["queryStringParameters"]['date_range']

        from_date = format_date(datetime.today() - timedelta(days=int(date_range)))

        # Add error response if date range is longer than a certain quantity?

      # If no date param given, set to 90 days
      else:
        from_date = format_date(datetime.today() - timedelta(days=int(90)))

    items = pull_words_with_params(list_id, from_date, todays_date)

  # If no params passed, get all lists words from the last 30 days
  else:
    items = pull_words_no_params(todays_date)

  return {
          'statusCode': 200,
          'headers': {
              'Access-Control-Allow-Methods': 'GET,OPTIONS',
              # 'Access-Control-Allow-Origin': os.environ['DomainName'],
              'Access-Control-Allow-Origin': '*',
          },
          'body': json.dumps(items)
        }

def pull_words_with_params(list_id, from_date, todays_date):

  try:
      response = table.query(
        KeyConditionExpression=Key('ListId').eq(list_id) & Key('Date').between(str(from_date),str(todays_date))
      )
  except ClientError as e:
    print(e.response['Error']['Message'])
  else:
    items = response['Items']
    print(json.dumps(items, indent=4))

  return {list_id : items}

def pull_words_no_params(todays_date):

  completed_item_list = {}

  from_date = format_date(datetime.today() - timedelta(days=int(7)))

  for list_id in all_lists:
    try:
        response = table.query(
          KeyConditionExpression=Key('ListId').eq(list_id) & Key('Date').between(str(from_date),str(todays_date))
        )
    except ClientError as e:
      print(e.response['Error']['Message'])
    else:
      completed_item_list[list_id] = response['Items']

  print(json.dumps(completed_item_list, indent=4))
  return completed_item_list

def format_date(date_object):

  formatted_date = date_object.strftime('%Y-%m-%d')

  return formatted_date