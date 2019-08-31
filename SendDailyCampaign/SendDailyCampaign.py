import os
import io
import csv
import json
import time
import boto3
from datetime import datetime
from botocore.vendored import requests

import sys
sys.path.insert(0, '/opt')
from vocab_random_word import select_random_word
from contact_lists import get_contact_level_list

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')
lambda_client = boto3.client('lambda')
dynamo_client = boto3.client('dynamodb')

# Cache contact level list
contact_level_list = get_contact_level_list()

# For each HSK level: Get a random word, fill in email template, create and send a campaign, send error notification on failure
def lambda_handler(event, context):

    # Loop through HSK levels
    for level_dict in contact_level_list:

        try: 

            level = level_dict["hsk_level"]

            # Get a random word for each level
            word = select_random_word(level)
            num_level = int(level)

            # Write to Dynamo
            store_word(word,num_level)

            # Replace campaign HTML placeholders with word and level
            campaign_contents = assemble_html_content(word,level,num_level)

            # Assemble create campaign API call payload
            payload = assemble_payload(campaign_contents,level,level_dict)
            
            print(f"HSK Level {num_level} campaign payload: {payload}")

            # SendGrid requires campaigns to be created and then sent
            # First create the campaign and retrieve the campaign id to call the send API
            campaign_id = create_campaign(payload)
            
            sendgrid_response = send_campaign(campaign_id)

            # Send success/error response and notification
            if "status" in sendgrid_response and sendgrid_response["status"] == "Scheduled":
                print(f"Campaign {sendgrid_response['id']} for HSK Level {num_level} scheduled for send successfully.")
            
            else: 
                failure_message = f"Campaign for {num_level} did not schedule successfully. SendGrid API response: " + sendgrid_response

                print (failure_message)
        
        except Exception as e:
            print(e)

def store_word(word,list_id):

    table = os.environ['TABLE_NAME']
    
    # Test date
    date = datetime.today()
    # Actual date
    # date = datetime.today()

    response = table.put_item(
        Item={
                'ListId': list_id,
                'Date': date,
                'Word': word,
            }
        )

    print("Word added to table.")

# There are placeholders in the example template for dynamic content like the daily word
# Here we swap the relevant content in for those placeholders
def assemble_html_content(word,level,num_level):

    # Create example sentence URL
    if num_level in range(1,4):
        example_link = "https://www.yellowbridge.com/chinese/sentsearch.php?word=" + word["Word"]

    else: 
        example_link = "https://fanyi.baidu.com/#zh/en/" + word["Word"]

    # We have an html template file packaged with this function's code which we read here
    with open('template.html') as fh:
        contents = fh.read()

    # Replace relevant content in example template
    campaign_contents = contents.replace("{word}", word["Word"])
    campaign_contents = campaign_contents.replace("{pronunciation}", word["Pronunciation"])
    campaign_contents = campaign_contents.replace("{definition}", word["Definition"])
    campaign_contents = campaign_contents.replace("{link}", example_link)
    campaign_contents = campaign_contents.replace("{level}", "HSK Level " + level)

    return campaign_contents

# Assemble create campaign payload
def assemble_payload(campaign_contents,level,level_dict):

    payload = {
        "title": "Daily vocab message - HSK Level " + level,
        "subject": "Daily vocab word - " + datetime.today().strftime('%b. %d, %Y'),
        "sender_id": 465706,
        "suppression_group_id": level_dict["unsub"],
        "list_ids": [
            level_dict["level_contact_list"]
        ],
        "html_content": campaign_contents
    }
    
    return payload

# Create campaign
def create_campaign(payload):
    
    # Create campaign API call
    create_url = "https://api.sendgrid.com/v3/campaigns"
        
    headers = {
        'authorization' : "Bearer " + os.environ['SG_API_KEY'],
        'content-type' : "application/json"
    }

    response = requests.request("POST", create_url, json=payload, headers=headers)
    
    print("Create campaign response:", response.text)

    data = response.json()
    campaign_id = data["id"]
    
    return campaign_id

# Send campaign
def send_campaign(campaign_id):
    
    # Send Campaign API call
    send_url = "https://api.sendgrid.com/v3/campaigns/" + str(campaign_id) + "/schedules/now"
        
    payload = "null"
    headers = {'authorization': 'Bearer ' + os.environ['SG_API_KEY']}

    response = requests.request("POST", send_url, json=payload, headers=headers)

    return response.json()