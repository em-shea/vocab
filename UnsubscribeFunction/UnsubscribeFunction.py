import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamo_client = boto3.resource('dynamodb')
table = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])

# Unsubscribe a user from the given HSK level or all levels.
def lambda_handler(event, context):

    body = json.loads(event["body"])

    # Extract relevant user details
    email_address = body['email']
    hsk_level = body['level']

    # Call Dynamo to check if user is subscribed to the given level
    subscriber_list = find_contact(email_address, hsk_level)
    # print("Found contacts: ", contact_found_count)

    unsubscribe_user(subscriber_list)

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
      for level_list in range(0,6):
        keys.append({
          'ListId': str(level_list+1),
          'SubscriberEmail': email_address
        })

    # If unsubscribing from a single list, get item from Dynamo by subscriber email and the given HSK level list
    else:
      keys.append({
          'ListId': hsk_level,
          'SubscriberEmail': email_address
        })

    # Batch get item from Dynamo
    try:
      response = dynamo_client.batch_get_item(
        RequestItems={
          table.name : {
            'Keys' : keys
          }
        }
      )
    except ClientError as e:
      print(e.response['Error']['Message'])
    else:
      print(response)
      # contact_found_count = len(response["Responses"][table.name])

    return response["Responses"][table.name]

def unsubscribe_user(subscriber_list):

    # If user does exist, change subscribed status to unsubscribed
    # If no users in subscriber_list, the loop will do nothing
    for item in subscriber_list:
      unsub_response = table.update_item(
        Key = {
          "SubscriberEmail": item["SubscriberEmail"],
          "ListId": item["ListId"]
        },
        UpdateExpression = "set #s = :status",
        ExpressionAttributeValues = {
          ":status": "unsubscribed"
        },
        ExpressionAttributeNames = {
          "#s": "Status"
        },
        ReturnValues = "UPDATED_NEW"
      )
      # print("Updated contact...", unsub_response)
