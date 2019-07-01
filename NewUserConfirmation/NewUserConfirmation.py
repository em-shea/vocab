import os
from botocore.vendored import requests

""" Invoked asynchronously from SubscribeFunction """

# Send subscribe confirmation email to new user
def lambda_handler(event, context):
    
    user_details = get_email_and_level(event)
    
    response = send_confirmation(user_details)
    code = response.status_code

    if code == 202:
        print(f"Response code {code}. Confirmation email successfully sent.")
    else:
        print(f"Response code {code}. Confirmation email unsuccessful.")

# Extract user selected email and level from queryStringParameters
def get_email_and_level(event):
    
    email_address = event["queryStringParameters"]['email']
    hsk_level = event["queryStringParameters"]['level']

    return email_address, hsk_level

# Put together email personalizations and call SendGrid send email API 
def send_confirmation(user_details):

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