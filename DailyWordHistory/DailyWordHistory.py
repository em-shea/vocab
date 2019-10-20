import os
import json
import boto3
from datetime import datetime
from datetime import timedelta
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamo = boto3.resource('dynamodb')

def lambda_handler(event,context):

  table = dynamo.Table(os.environ['TABLE_NAME'])

  items = []

  from_date = datetime.today() - timedelta(days=int(90))

  from_date = format_date(from_date)
  todays_date = format_date(datetime.today())

  # Filter data by query string parameters
  # Query string parameters should be a the list name (ex, HSKLevel1) and a number of days (ex, 7)
  if 'queryStringParameters' in event:

    # Filter by word list
    if 'list' in event['queryStringParameters']:
      list_id = event["queryStringParameters"]['list']

      # Filter by number of days to include
      if 'date_range' in event["queryStringParameters"]:
        date_range = event["queryStringParameters"]['date_range']

        # Subtract days to get date range
        from_date = datetime.today() - timedelta(days=int(date_range))

        from_date = format_date(from_date)
        todays_date = format_date(datetime.today())

        try:
            response = table.query(
                KeyConditionExpression=Key('ListId').eq(list_id) & Key('Date').between(str(from_date),str(todays_date))
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            items = response['Items']
            print(json.dumps(items, indent=4))

            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Methods': 'GET,OPTIONS',
                    # 'Access-Control-Allow-Origin': os.environ['DomainName'],
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps(items)
            }

      # If no date range supplied, get words from last 90 days
      else:
          try:
              response = table.query(
                  KeyConditionExpression=Key('ListId').eq(list_id) & Key('Date').between(str(from_date),str(todays_date))
              )
          except ClientError as e:
              print(e.response['Error']['Message'])
          else:
              items = response['Items']
              print(json.dumps(items, indent=4))

              return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Methods': 'GET,OPTIONS',
                    # 'Access-Control-Allow-Origin': os.environ['DomainName'],
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps(items)
            }

  # If no list or date range supplied, get all lists words from the last 30 days
  else:
      try:
          response = table.query(
            KeyConditionExpression=Key('ListId').between('HSKLevel1','HSKLevel6') & Key('Date').between(str(from_date),str(todays_date))
          )
      except ClientError as e:
          print(e.response['Error']['Message'])
      else:
          items = response['Items']
          print(json.dumps(items, indent=4))
          return items

  return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            # 'Access-Control-Allow-Origin': os.environ['DomainName'],
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(items)
    }

def format_date(date_object):

  formatted_date = date_object.strftime('%Y-%m-%d')

  return formatted_date