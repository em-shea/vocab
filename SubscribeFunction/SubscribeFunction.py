import os
import json
import boto3
from botocore.vendored import requests

lambda_client = boto3.client('lambda')

def add_to_contact_list(recipient_id, hsk_level):

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

    url = "https://api.sendgrid.com/v3/contactdb/lists/" + str(list_id) + "/recipients/" + str(recipient_id)

    payload = "null"
    headers = {'authorization': 'Bearer ' + os.environ['SG_API_KEY']}

    response = requests.request("POST", url, data=payload, headers=headers)
    
    print(response)

def lambda_handler(event, context):
  
    # extract relevant user details
    email_address = event["queryStringParameters"]['email']
    hsk_level = event["queryStringParameters"]['level']

    # create payload with user details
    payload = [
        {
            "email" : email_address,
            "level_list" : "Level" + hsk_level
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

    # Call function to add new contact to list
    add_to_contact_list(recipient_id, int(hsk_level))

    # Call function send confirmation email
    invoke_response = lambda_client.invoke(
        FunctionName="NewUserConfirmation",
        InvocationType='Event',
        Payload=json.dumps({
            "hsk_level": event
        })
    )

    code = invoke_response['StatusCode']

    if code == 202:
        print(f"Response code {code}. Invoke confirmation function successful.")
    else:
        print(f"Response code {code}. Invoke confirmation function unsuccessful.")

    return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Origin': '*',
            },
            'body': '{"success" : true}'
        }