import os
import json
import boto3
from botocore.vendored import requests
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamo_client = boto3.resource('dynamodb')
table = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])
table_name = dynamo_client.Table(os.environ['TABLE_NAME'])

# Unsubscribe a user from the given HSK level or all levels.
def lambda_handler(event, context):

    body = json.loads(event["body"])

    # Extract relevant user details
    email_address = body['email']
    hsk_level = body['level']

    # Call Dynamo to check if user is subscribed to the given level
    response, contact_found_count = find_contact(email_address, hsk_level)
    print("Found contacts: ", contact_found_count)

    unsubscribe_user(response, contact_found_count)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : true}'
      }

def find_contact(email_address, hsk_level):

    keys = []

    # If unsubscribing from all lists, get item from Dynamo by subscriber email and each HSK level list
    if hsk_level == "all":

      # Generate a list of all HSK level keys
      for level_list in range(0,5):
        keys.append({
          'ListId': str(level_list+1),
          'SubscriberEmail': email_address
        })
    else:

      # If unsubscribing from a single list, get item from Dynamo by subscriber email and the given HSK level list
      keys = keys.append({
          'ListId': hsk_level,
          'SubscriberEmail': email_address
        })

      try:

        # Batch get item from Dynamo
        response = dynamo_client.batch_get_item(
          RequestItems={
            table_name : {
              'Keys' : keys
            }
          }
        )
      except ClientError as e:
        print(e.response['Error']['Message'])
      else:
        print(response)
        contact_found_count = len(response["Responses"][table])

    return response, contact_found_count

def unsubscribe_user(response, contact_found_count):

    # If user does not exist, return success anyways for security
    if contact_found_count == 0:
      return

    # If user does exist, change subscribed status to unsubscribed
    if contact_found_count != 0:
      for item in response["Responses"][table]:
        response = dynamo_client.update_item(
          TableName = table,
          Key = {
            "SubscriberEmail": item["SubscriberEmail"],
            "ListId": item["ListId"]
          },
          UpdateExpression = "set Status = :status",
          ExpressionAttributeValues = {
            ":status": "unsubscribed"
          },
          ExpressionAttributeNames = {
            "#s": "Status"
          },
          ReturnValues = "UPDATED_NEW"
        )
        print("Updated contact...", response)
      return
