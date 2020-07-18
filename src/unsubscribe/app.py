import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# region_name specified in order to mock in unit tests
dynamo_client = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Unsubscribe a user from the given HSK level or all levels.
def lambda_handler(event, context):

    body = json.loads(event["body"])

    # Extract relevant user details
    email_address = body['email']
    list_id = body['list']
    
    if list_id != "all":
      hsk_level = list_id[0]
      char_set = list_id[2:]

    # Call Dynamo to check if user is subscribed to the given level
    contact_keys = list_contacts(email_address, list_id)
    subscriber_list = get_dynamo_contacts(contact_keys)
    # print("Found contacts: ", contact_found_count)

    # If user does exist, change subscribed status to unsubscribed
    # If no users in subscriber_list, do nothing
    for user in subscriber_list:
      unsubscribe_user(user)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : true}'
      }

def list_contacts(email_address, list_id):

    keys = []

    # If unsubscribing from all lists, get item from Dynamo by subscriber email and each HSK level list
    if list_id == "all":

      # Generate a list of all HSK level keys
      for level_list in range(0,6):
        keys.append({
          'ListId': f"{level_list + 1}-simplified",
          'SubscriberEmail': email_address
        })
        keys.append({
          'ListId': f"{level_list + 1}-traditional",
          'SubscriberEmail': email_address
        })

    # If unsubscribing from a single list, get item from Dynamo by subscriber email and the given HSK level list
    else:
      keys.append({
          'ListId': list_id,
          'SubscriberEmail': email_address
        })
    
    print(keys)
    return keys

def get_dynamo_contacts(contact_keys):

    # Batch get item from Dynamo
    try:
      response = dynamo_client.batch_get_item(
        RequestItems={
          table.name : {
            'Keys' : contact_keys
          }
        }
      )
    except ClientError as e:
      print(e.response['Error']['Message'])
    else:
      print(response)
      # contact_found_count = len(response["Responses"][table.name])

    return response["Responses"][table.name]

def unsubscribe_user(user):

    unsub_response = table.update_item(
      Key = {
        "SubscriberEmail": user["SubscriberEmail"],
        "ListId": user["ListId"]
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
