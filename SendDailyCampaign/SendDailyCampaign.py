import json
import boto3
import os
import time
from datetime import datetime
from botocore.vendored import requests

lambda_client = boto3.client('lambda')
sns_client = boto3.client('sns')

# For each HSK level: Get a random word, fill in email template, create and send a campaign, send error notification on failure
def lambda_handler(event, context):

    # Loop through HSK levels
    for level_dict in get_level_list():

        try: 

            level = level_dict["hsk_level"]

            # Get a random word for each level
            word = get_random(level)
            num_level = int(level)

            # Replace campaign HTML placeholders with word and level
            campaign_contents = assemble_html_content(word,level,num_level)

            # Assemble create campaign API call payload
            payload = assemble_payload(campaign_contents,level,level_dict)
            
            # SendGrid requires campaigns to be created and then sent
            # First create the campaign and retrieve the campaign id to call the send API
            campaign_id = create_campaign(payload)
            
            sendgrid_response = send_campaign(campaign_id)

            # Send success/error response and notification
            if "status" in sendgrid_response and sendgrid_response["status"] == "Scheduled":
                print(f"Campaign {sendgrid_response['id']} for HSK Level {num_level} scheduled for send successfully.")
            
            else: 
                failure_message = f"Campaign for {num_level} did not schedule successfully. SendGrid API response: " + sendgrid_response
                publish_sns_update(failure_message)

                print (failure_message)
        
        except Exception as e:
            print(e)

# Send SNS notification if the send campaign API call fails
def publish_sns_update(message):

    response = sns_client.publish(
        TargetArn = os.environ['SUB_TOPIC_ARN'], 
        Message=json.dumps({'default': message}),
        MessageStructure='json'
    )

# Get SendGrid level list data: list ID and unsubscribe group ID for each HSK level 
def get_level_list():

    hsk_level_lists = [{
        "hsk_level": "1",
        "level_contact_list": 7697668,
        "unsub": 84947
    },{
        "hsk_level": "2",
        "level_contact_list": 8295693,
        "unsub": 84956
    },{
        "hsk_level": "3",
        "level_contact_list": 8296149,
        "unsub": 84957
    },{
        "hsk_level": "4",
        "level_contact_list": 8296153,
        "unsub": 84958
    },{
        "hsk_level": "5",
        "level_contact_list": 8393613,
        "unsub": 84959
    },{
        "hsk_level": "6",
        "level_contact_list": 8393614,
        "unsub": 84960
    }]

    return hsk_level_lists

# Get a random word for a given level
def get_random(any_level):
    invoke_response = lambda_client.invoke(
        FunctionName="VocabRandomEntry",
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "hsk_level": any_level
        })
    )

    response_json = invoke_response['Payload'].read()
    response_python = json.loads(response_json)
    word = response_python["body"]
    return word

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