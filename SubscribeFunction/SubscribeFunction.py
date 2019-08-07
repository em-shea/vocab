import os
import json
import boto3
from botocore.vendored import requests

lambda_client = boto3.client('lambda')

sns_client = boto3.client('sns')

# Subscribe a new user, including sending an email confirmation to the user and a notification to the app owner
def lambda_handler(event, context):
  
    # Extract relevant user details
    email_address = event["queryStringParameters"]['email']
    hsk_level = event["queryStringParameters"]['level']

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

    # Add new contact to the correct HSK level list
    add_to_contact_list(recipient_id, int(hsk_level))

    # Send confirmation email function call
    confirmation_response = send_new_user_confirmation_email(email_address, hsk_level)

    # Check if confirmation email function invoked successfully
    code = confirmation_response['StatusCode']

    if code == 202:
        success_status = True
        
        print(f"Response code {code}. Invoke confirmation function successful.")

    else:
        success_status = False

        print(f"Response code {code}. Invoke confirmation function unsuccessful.")

    # Send notification to an SNS queue to notify the app owner
    publish_sns_update(success_status,payload)

    return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Origin': '*',
            },
            'body': '{"success" : true}'
        }

# Add created contact to the correct HSK level
def add_to_contact_list(recipient_id, hsk_level):

    # SendGrid level list IDs
    list_ids = [
        {
            "id": 7697668,
            "name": "Level 1"
        },
        {
            "id": 8295693,
            "name": "Level 2"
        },
        {
            "id": 8296149,
            "name": "Level 3"
        },
        {
            "id": 8296153,
            "name": "Level 4"
        },
        {
            "id": 8393613,
            "name": "Level 5"
        },
        {
            "id": 8393614,
            "name": "Level 6"
        }
    ]

    hsk_level_index = hsk_level - 1

    list_id = list_ids[hsk_level_index]["id"]

    # Call add contact to list API
    url = "https://api.sendgrid.com/v3/contactdb/lists/" + str(list_id) + "/recipients/" + str(recipient_id)

    payload = "null"
    headers = {'authorization': 'Bearer ' + os.environ['SG_API_KEY']}

    response = requests.request("POST", url, data=payload, headers=headers)

    print(response)

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

# Publish an SNS message to notify the app owner about the new user creation success/failure
def publish_sns_update(success_status,payload):

    if success_status == True:
        message = f"Success - {payload[0]['email']} successfully subscribed to {payload[0]['level_list']}"
    else:
        message = f"Error - {payload[0]['email']} not subscribed to {payload[0]['level_list']}"

    response = sns_client.publish(
        TargetArn = os.environ['SUB_TOPIC_ARN'], 
        Message=json.dumps({'default': message}),
        MessageStructure='json'
    )

    print("SNS Response", response)