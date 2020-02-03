import os
import json
import boto3
from datetime import datetime

import sys
sys.path.insert(0, '/opt')

sns_client = boto3.client('sns')
ses_client = boto3.client('ses')
lambda_client = boto3.client('lambda')
dynamo_client = boto3.resource('dynamodb')

# Subscribe a new user, including sending an email confirmation to the user and a notification to the app owner
def lambda_handler(event, context):

    body = json.loads(event["body"])

    # Extract relevant user details
    email_address = body['email']
    hsk_level = body['level']

    # Write contact to DynamoDB
    try:
        create_contact_dynamo(email_address, hsk_level)
        print(f"Success: Contact created in Dynamo - {email_address}, {hsk_level}.")
    except Exception as e:
        print(f"Error: Failed to create contact in Dynamo - {email_address}, {hsk_level}.")
        print(e)
        return {
            'statusCode': 502,
            'headers': {
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Origin': '*',
            },
            'body': '{"success" : false}'
        }

    # Send confirmation email from SES
    try:
        send_new_user_confirmation_email_ses(email_address, hsk_level)
        print(f"Success: Confirmation email sent through SES - {email_address}, {hsk_level}.")
    except Exception as e:
        print(f"Error: Failed to send confirmation email through SES - {email_address}, {hsk_level}.")
        print(e)
        return {
            'statusCode': 502,
            'headers': {
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Origin': '*',
            },
            'body': '{"success" : false}'
        }

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : true}'
    }

# Write new contact to Dynamo
def create_contact_dynamo(email_address, hsk_level):

    table = dynamo_client.Table(os.environ['TABLE_NAME'])

    date = str(datetime.today().strftime('%Y-%m-%d'))

    sub_status = "subscribed"

    character_set = "simplified"

    response = table.put_item(
        Item={
                'ListId': hsk_level,
                'SubscriberEmail' : email_address,
                'DateSubscribed': date,
                'Status': sub_status,
                'CharacterSet' : character_set
            }
        )

    print(f"Contact added to Dynamo - {email_address}, {hsk_level}.")

def send_new_user_confirmation_email_ses(email_address, hsk_level):

    # We have an html template file packaged with this function's code which we read here
    with open('confirmation_template.html') as fh:
        contents = fh.read()

    email_contents = contents.replace("{level}", hsk_level)

    payload = ses_client.send_email(
        Source = "Haohaotiantian <welcome@haohaotiantian.com>",
        Destination = {
            "ToAddresses" : [
            email_address
            ]
        },
        Message = {
            "Subject": {
                "Charset": "UTF-8",
                "Data": "Welcome! 欢迎您!"
                },
            "Body": {
                "Html": {
                    "Charset": "UTF-8",
                    "Data": email_contents
                }
            }
        }
    )