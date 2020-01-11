import os
import json
import boto3
from datetime import datetime
from botocore.vendored import requests

import sys
sys.path.insert(0, '/opt')
from contact_lists import get_contact_level_list

sns_client = boto3.client('sns')
ses_client = boto3.client('ses')
lambda_client = boto3.client('lambda')
dynamo_client = boto3.resource('dynamodb')

# Cache contact level list
contact_level_list = get_contact_level_list()

# Subscribe a new user, including sending an email confirmation to the user and a notification to the app owner
def lambda_handler(event, context):

    body = json.loads(event["body"])

    # Extract relevant user details
    email_address = body['email']
    hsk_level = body['level']

    # # Create contact and return contact ID
    # try:
    #     recipient_id = create_contact(email_address, hsk_level)
    # except Exception as e:
    #     print(f"Error: Failed to create contact for {email_address} for {hsk_level}")
    #     print(e)
    #     return {
    #         'statusCode': 502,
    #         'headers': {
    #             'Access-Control-Allow-Methods': 'POST,OPTIONS',
    #             'Access-Control-Allow-Origin': '*',
    #         },
    #         'body': '{"success" : false}'
    #     }

    # # Add new contact to the correct HSK level list
    # try:
    #     add_to_contact_list(recipient_id, int(hsk_level))
    # except Exception as e:
    #     print(f"Error: Failed to add contact {email_address} to {hsk_level} list")
    #     print(e)
    #     return {
    #         'statusCode': 502,
    #         'headers': {
    #             'Access-Control-Allow-Methods': 'POST,OPTIONS',
    #             'Access-Control-Allow-Origin': '*',
    #         },
    #         'body': '{"success" : false}'
    #     }

    # # Send confirmation email function call
    # try:
    #     send_new_user_confirmation_email(email_address, hsk_level)
    #     print(f"Success: {email_address} subscribed to {hsk_level}")
    # except Exception as e:
    #     print(f"Error: Failed to send confirmation email to {email_address} for {hsk_level}.")
    #     print(e)
    #     return {
    #         'statusCode': 502,
    #         'headers': {
    #             'Access-Control-Allow-Methods': 'POST,OPTIONS',
    #             'Access-Control-Allow-Origin': '*',
    #         },
    #         'body': '{"success" : false}'
    #     }

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
                'Date': date,
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
        Source = "welcome@haohaotiantian.com",
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
                # "Text": {
                #     "Charset": "UTF-8",
                #     "Data": "test html api send"
                # },
                "Html": {
                    "Charset": "UTF-8",
                    "Data": email_contents
                }
            }
        }
    )


# Create new contact
def create_contact(email_address, hsk_level):

    # Create payload with user details
    payload = [
        {
            "email" : email_address,
            "level_list" : "Level " + hsk_level
        }
    ]

    # SendGrid create contact API endpoint and API key
    url = "https://api.sendgrid.com/v3/contactdb/recipients"

    headers = {
        'authorization' : "Bearer " + os.environ['SG_API_KEY'],
        'content-type' : "application/json"
    }

    # Send POST request
    response = requests.request("POST", url, json=payload, headers=headers)

    # Collect ID from newly created contact
    data = response.json()
    recipient_id = data["persisted_recipients"][0]

    return recipient_id

# Add created contact to the correct HSK level
def add_to_contact_list(recipient_id, hsk_level):

    hsk_level_index = hsk_level - 1

    list_id = contact_level_list[hsk_level_index]["level_contact_list"]

    # Call add contact to list API
    url = "https://api.sendgrid.com/v3/contactdb/lists/" + str(list_id) + "/recipients/" + str(recipient_id)

    payload = "null"
    headers = {'authorization': 'Bearer ' + os.environ['SG_API_KEY']}

    response = requests.request("POST", url, data=payload, headers=headers)

    return response

# Send subscribe confirmation email to new user
def send_new_user_confirmation_email(email_address, hsk_level):

    user_details = email_address, hsk_level

    response = generate_confirmation_email_content_and_send(user_details)
    code = response.status_code

    if code == 202:
        print(f"Response code {code}. Confirmation email successfully sent.")
    else:
        print(f"Response code {code}. Confirmation email unsuccessful.")

    return response

# Put together email personalizations and call SendGrid send email API
def generate_confirmation_email_content_and_send(user_details):

    email_address, hsk_level = user_details

    url = "https://api.sendgrid.com/v3/mail/send"

    payload = {
        "personalizations": [
            {
            "to": [
                {
                "email": email_address
                }
            ],
            "dynamic_template_data": {
                "level": hsk_level,
            },
            "subject": "Hello, World!"
            }
        ],
        "from": {
            "email": "vocab@haohaotiantian.com"
        },
        "reply_to": {
            "email": "vocab@haohaotiantian.com"
        },
        "template_id": "d-6c1a22b11b4a4f3dbe3826d5e70be4cc"
        }

    headers = {
    'authorization': "Bearer " + os.environ['SG_API_KEY'],
    'content-type': "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    return response