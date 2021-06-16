import os
import io
import csv
import json
import time
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

import sys
sys.path.insert(0, '/opt')
from vocab_random_word import select_random_word

# region_name specified in order to mock in unit tests
ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION'])
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['DYNAMODB_TABLE_NAME'])

# sns_client = boto3.client('sns', region_name=os.environ['AWS_REGION'])
# word_history_table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])
# contacts_table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['CONTACT_TABLE_NAME'])


# Select a random word for each HSK level and store in word history Dynamo table 
# Loop through list of contacts, assemble a customized email, and send
# Log each send and send error notification on failure
def lambda_handler(event, context):

    # Select a random word for each level
    word_list = get_daily_words()

    # If unable to store word in Dynamo, continue sending emails
    # try:
    #     # Write to Dynamo
    #     store_words(word_list)
    # except Exception as e:
    #     print(e)

    todays_announcement_html = get_announcement()

    # Scan the contacts table for a list of all contacts
    all_contacts = get_users_and_subscriptions()

    # contact item example:
    # {'Date': '2020-01-13', 'CharacterSet': 'simplified', 'Status': 'unsubscribed', 'SubscriberEmail': 'user@example.com', 'ListId': '1'}

    # for contact in all_contacts:

    #     # Send emails to all subscribed contacts
    #     if not contact['Status'] == 'unsubscribed':
    #         partial_email = contact['SubscriberEmail'][0:5]
    #         list_id = contact['ListId']
    #         email = contact['SubscriberEmail']
    #         print("Subscribed contact: ", partial_email, list_id)

    #         word_index = int(contact['ListId'][0]) - 1

    #         hsk_level = list_id[0]
    #         char_set = contact['CharacterSet']

    #         word = word_list[word_index]

    #         # If the get_daily_words() hit an error and did not select a word for a given HSK level,
    #         # word will be None. If so, do not send an email.
    #         if word is not None:

    #             campaign_contents = assemble_html_content(hsk_level, email, word, char_set, todays_announcement_html)

    #             try:
    #                 response = send_email(campaign_contents, email)
    #             except Exception as e:
    #                 print(f"Error: Failed to send email - {partial_email}, {list_id}.")
    #                 print(e)

def get_announcement():

    todays_date = str(datetime.today().strftime('%Y-%m-%d'))
    file_name = todays_date + ".json"

    s3 = boto3.client('s3')

    announcement_file_message = ""

    try:
        s3_file = s3.get_object(Bucket=os.environ['ANNOUNCEMENTS_BUCKET'], Key=file_name)
    except Exception as e:
        # Return None if file not found or other error
        return None
    else:
        s3_file_content = s3_file['Body'].read().decode('utf-8')
        json_content = json.loads(s3_file_content)
        announcement_file_message = json_content['message']

        # We have an html template file packaged with this function's code which we read here
        # To run unit tests for this function, we need to specify an absolute file path
        abs_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(abs_dir, 'announcements.html')) as fh:
            announcement_html = fh.read()

        announcement_html = announcement_html.replace("{announcement_message}", announcement_file_message)
        return announcement_html

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

def get_users_and_subscriptions():

    users_and_subscriptions = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GS1PK').eq('USER')
    )
    return users_and_subscriptions

    # Loop through contacts in Dynamo
    results = contacts_table.scan(
        Select = "ALL_ATTRIBUTES"
    )

    all_contacts = results['Items']

    return all_contacts

# Populate relevant content in for the placeholders in the email template
def assemble_html_content(hsk_level, email, word, char_set, todays_announcement_html):

    # Select simplified or traditional character 
    if char_set == "simplified":
        selected_word = word["Word"]
    else:
        selected_word = word["Word-Traditional"]

    num_level = int(hsk_level)

    # Create example sentence URL
    if num_level in range(1,4):
        example_link = "https://www.yellowbridge.com/chinese/sentsearch.php?word=" + selected_word

    else:
        example_link = "https://fanyi.baidu.com/#zh/en/" + selected_word

    # We have an html template file packaged with this function's code which we read here
    # To run unit tests for this function, we need to specify an absolute file path
    abs_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(abs_dir, 'template.html')) as fh:
        contents = fh.read()

    # Replace relevant content in example template
    campaign_contents = contents.replace("{word}", selected_word)
    campaign_contents = campaign_contents.replace("{pronunciation}", word["Pronunciation"])
    campaign_contents = campaign_contents.replace("{definition}", word["Definition"])
    campaign_contents = campaign_contents.replace("{link}", example_link)
    campaign_contents = campaign_contents.replace("{level}", "HSK Level " + hsk_level)
    campaign_contents = campaign_contents.replace("{quiz_link}", "https://haohaotiantian.com/quiz?list=HSKLevel" + hsk_level + "&days=14&ques=10&char=" + char_set)
    campaign_contents = campaign_contents.replace("{history_link}", "https://haohaotiantian.com/history?list=HSKLevel" + hsk_level + "&dates=30&char=" + char_set)
    campaign_contents = campaign_contents.replace("{unsubscribe_link}", "https://haohaotiantian.com/unsub?level=" + hsk_level + "&email=" + email + "&char=" + char_set)
    if todays_announcement_html is not None:
        campaign_contents = campaign_contents.replace("{announcement_slot}", todays_announcement_html)
    else:
        campaign_contents = campaign_contents.replace("{announcement_slot}", "")

    return campaign_contents

# Send SES email
def send_email(campaign_contents, email):

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

    return response