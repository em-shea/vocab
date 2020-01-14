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
dynamo_client = boto3.resource('dynamodb')
word_history_table = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])
contacts_table = boto3.resource('dynamodb').Table(os.environ['CONTACT_TABLE_NAME'])

# For each HSK level: Get a random word, fill in email template, create and send a campaign, send error notification on failure
def lambda_handler(event, context):

    # Select a random word for each level
    word_list = get_daily_word()

    # If unable to store word in Dynamo, continue sending campaign
    try:

        # Write to Dynamo
        store_word(word_list)

    except Exception as e:
        print(e)

    print(word_list)

    # Scan the contacts table for a list of all contacts
    all_contacts = scan_contacts_table()

    # Assemble HTML content and send the ses email for each contact
    response = send_all_emails(word_list, all_contacts)

def get_daily_word():

    # Create list of words for the day
    word_list = []

    # Loop through HSK levels and select and save word
    for hsk_level in range(0,6):

        level = str(hsk_level + 1)

        try:

            # Get a random word for each level
            word = select_random_word(level)
            num_level = int(level)

            word_list.append(word)

        except Exception as e:
            print(e)

    return(word_list)

def store_word(word_list):

    # Loop through all words for the day
    for item in word_list:

        word = item
        level = item['HSK Level']

        list_id = "HSKLevel" + level

        date = str(datetime.today().strftime('%Y-%m-%d'))

        # Write each to Dynamo word history table
        response = word_history_table.put_item(
            Item={
                    'ListId': list_id,
                    'Date': date,
                    'Word': word,
                }
            )

        # individual_word = item['Word']
        # print(f"Response from word history table for {individual_word}, {level}...", response['ResponseMetadata']['HTTPStatusCode'])

    return

def scan_contacts_table():

    # Loop through contacts in Dynamo
    results = contacts_table.scan(
        Select = "ALL_ATTRIBUTES"
    )

    all_contacts = results['Items']

    return all_contacts

def send_all_emails(word_list, all_contacts):

    # example:
    # {'Date': '2020-01-13', 'CharacterSet': 'simplified', 'Status': 'unsubscribed', 'SubscriberEmail': 'c.emilyshea@gmail.com', 'ListId': '1'}

    for contact in all_contacts:
        if contact['Status'] == 'unsubscribed':
            return
        else:
            level = contact['ListId']
            email = contact['SubscriberEmail']

            word_index = int(contact['ListId']) - 1
            word = word_list[word_index]
            campaign_contents = assemble_html_content(level, email, word)
            response = send_email(campaign_contents, email, level)

# Swap the relevant content in for the placeholders in the email template
def assemble_html_content(level, email, word):

    num_level = int(level)

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
    campaign_contents = campaign_contents.replace("{history_link}", "https://haohaotiantian.com/history?list=HSKLevel" + level + "&dates=30")
    campaign_contents = campaign_contents.replace("{unsubscribe_link}", "https://haohaotiantian.com/unsub?level=" + level + "&email=" + email)

    return campaign_contents

# Send SES email
def send_email(campaign_contents, email, level):

    response = ses_client.send_email(
        Source = "vocab@haohaotiantian.com",
        Destination = {
            "ToAddresses" : [
            email
            ]
        },
        Message = {
            "Subject": {
            "Charset": "UTF-8",
            "Data": "Daily vocab word - " + datetime.today().strftime('%b. %d, %Y')
            },
            "Body": {
                "Html": {
                    "Charset": "UTF-8",
                    "Data": html
                }
            }
        }
    )

    return response