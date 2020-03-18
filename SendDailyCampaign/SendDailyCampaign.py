import os
import io
import csv
import json
import time
import boto3
from datetime import datetime

import sys
sys.path.insert(0, '/opt')
from vocab_random_word import select_random_word

s3_client = boto3.client('s3')
ses_client = boto3.client('ses')
sns_client = boto3.client('sns')
lambda_client = boto3.client('lambda')
dynamo_client = boto3.resource('dynamodb')
word_history_table = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])
contacts_table = boto3.resource('dynamodb').Table(os.environ['CONTACT_TABLE_NAME'])

# Select a random word for each HSK level and store in word history Dynamo table 
# Loop through list of contacts, assemble a customized email, and send
# Log each send and send error notification on failure
def lambda_handler(event, context):

    # Select a random word for each level
    word_list = get_daily_words()

    # If unable to store word in Dynamo, continue sending campaign
    try:

        # Write to Dynamo
        store_words(word_list)

    except Exception as e:
        print(e)

    # print("Word list for today...", word_list)

    # Scan the contacts table for a list of all contacts
    all_contacts = scan_contacts_table()
    # print("Contacts scanned...", all_contacts)

    # contact item example:
    # {'Date': '2020-01-13', 'CharacterSet': 'simplified', 'Status': 'unsubscribed', 'SubscriberEmail': 'c.emilyshea@gmail.com', 'ListId': '1'}

    for contact in all_contacts:

        # Send emails to all subscribed contacts
        if not contact['Status'] == 'unsubscribed':
            partial_email = contact['SubscriberEmail'][0:5]
            print("Subscribed contact:", partial_email)
            list_id = contact['ListId']
            email = contact['SubscriberEmail']

            word_index = int(contact['ListId'][0]) - 1
            # print("Word index:", word_index)

            hsk_level = list_id[0]
            char_set = contact['CharacterSet']

            word = word_list[word_index]
            # print("Word for contact:", word)

            # If the get_daily_words() hit an error and did not select a word for a given HSK level,
            # word will be None. If so, do not send an email.
            if word is not None:

                campaign_contents = assemble_html_content(hsk_level, email, word, char_set)

                try:
                    response = send_email(campaign_contents, email)
                except Exception as e:
                    print(f"Error: Failed to send email - {partial_email}, {list_id}.")
                    print(e)
            # else:
            #     print("Unsubscribed contact:", contact['SubscriberEmail'])
            #     pass

def get_daily_words():

    word_list = []

    # Loop through HSK levels and select word
    for hsk_level in range(0,6):
        level = str(hsk_level + 1)
        try:
            word = select_random_word(level)
            word_list.append(word)
        except Exception as e:
            # Appending None to the list as a placeholder for the level's word. Emails will not send for this level.
            word_list.append(None)
            print(e)

    return word_list

def store_words(word_list):

    for item in word_list:
        word = item
        level = item['HSK Level']
        list_id = "HSKLevel" + level
        date = str(datetime.today().strftime('%Y-%m-%d'))

        # Write each word to Dynamo word history table
        response = word_history_table.put_item(
            Item={
                    'ListId': list_id,
                    'Date': date,
                    'Word': word,
                }
            )

def scan_contacts_table():

    # print("Scanning contacts table...")

    # Loop through contacts in Dynamo
    results = contacts_table.scan(
        Select = "ALL_ATTRIBUTES"
    )

    all_contacts = results['Items']

    return all_contacts

# Populate relevant content in for the placeholders in the email template
def assemble_html_content(hsk_level, email, word, char_set):

    # Select simplified or traditional character 
    if char_set == "simplified":
        selected_word = word["Word"]
    else:
        selected_word = word["Word-Traditional"]

    # print("Assembling HTML content...")
    num_level = int(hsk_level)

    # Create example sentence URL
    if num_level in range(1,4):
        example_link = "https://www.yellowbridge.com/chinese/sentsearch.php?word=" + selected_word

    else:
        example_link = "https://fanyi.baidu.com/#zh/en/" + selected_word

    # We have an html template file packaged with this function's code which we read here
    with open('template.html') as fh:
        contents = fh.read()

    # Replace relevant content in example template
    campaign_contents = contents.replace("{word}", selected_word)
    campaign_contents = campaign_contents.replace("{pronunciation}", word["Pronunciation"])
    campaign_contents = campaign_contents.replace("{definition}", word["Definition"])
    campaign_contents = campaign_contents.replace("{link}", example_link)
    campaign_contents = campaign_contents.replace("{level}", "HSK Level " + hsk_level)
    campaign_contents = campaign_contents.replace("{history_link}", "https://haohaotiantian.com/history?list=HSKLevel" + hsk_level + "&dates=30")
    campaign_contents = campaign_contents.replace("{unsubscribe_link}", "https://haohaotiantian.com/unsub?level=" + hsk_level + "&email=" + email)

    return campaign_contents

# Send SES email
def send_email(campaign_contents, email):

    # print("Sending SES email...")
    response = ses_client.send_email(
        Source = "Haohaotiantian <vocab@haohaotiantian.com>",
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
                    "Data": campaign_contents
                }
            }
        }
    )

    # print("SES response", response)
    return response