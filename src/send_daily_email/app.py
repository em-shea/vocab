import os
import json
import boto3
from random import randint
from datetime import datetime
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

import user_service
import list_word_service
import vocab_list_service

# region_name specified in order to mock in unit tests
ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION'])
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['DYNAMODB_TABLE_NAME'])
word_history_table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):

    # Select a random word for each level
    todays_words = get_daily_words()

    # If unable to store word in Dynamo, continue sending emails
    try:
        # Write to Dynamo
        store_words(todays_words)
    except Exception as e:
        print(e)

    todays_announcement = get_announcement()

    user_list = user_service.get_all_users()

    email_counter = 0
    for user in user_list:
        active_subscription_count = 0
        for subscription in user.subscriptions:
            if subscription.status == 'subscribed':
                active_subscription_count += 1
        if active_subscription_count>0:
            email_content = assemble_html_content(user, todays_words, todays_announcement)
            try:
                # print('send emails')
                response = send_email(user, email_content)
                email_counter += 1
            except Exception as e:
                print(f"Error: Failed to send email - {user['user_data']['PK']}.")
                print(e)
    
    print(f"{email_counter} emails sent.")

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
        with open(os.path.join(abs_dir, 'announcements_template.html')) as fh:
            announcement_html = fh.read()

        announcement_html = announcement_html.replace("{announcement_message}", announcement_file_message)
        return announcement_html

def get_daily_words():
    print('getting daily words...')

    todays_words = {}

    all_lists = vocab_list_service.get_vocab_lists()

    for list in all_lists:
        try:
            all_words = list_word_service.get_words_in_list(list['list_id'])
            random_number = randint(0,len(all_words)-1)
            random_word = all_words[random_number]
            todays_words[list['list_id']] = random_word
        except Exception as e:
            todays_words[list['list_id']] = None
            print(e)

    print('daily words: ', todays_words)
    return todays_words

def store_words(todays_words):

    for list_id, word in todays_words.items():
        date = str(datetime.today().strftime('%Y-%m-%d'))

        try:
            response = table.put_item(
                Item={
                    'PK': 'LIST#' + list_id,
                    'SK': 'DATESENT#' + date,
                    'Word': word
                }
            )
        except Exception as e:
            print('Failed to store todays word: ', word)
            print('DynamoDB response: ', response)
            print(e)

def assemble_html_content(user, todays_words, todays_announcement):

    # Appends multiple words into the same email
    # TODO: Order the lists in some way?
    word_content = ""
    for subscription in user.subscriptions:
        if subscription.status == 'subscribed':
            word_content = word_content + assemble_word_html_content(user.email_address, subscription, todays_words)

    # Open HTML template file
    # To run unit tests, we need to specify an absolute file path
    abs_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(abs_dir, 'email_template.html')) as fh:
        email_template = fh.read()

    # Hard coding HSK level before list database refactor
    # Get first list user is subscribed to and use in unsub link
    email_contents = email_template.replace("{unsubscribe_link}", "https://haohaotiantian.com/unsub?list=" + user.subscriptions[0].list_id + "&char=" + user.subscriptions[0].character_set + "&email=" + user.email_address)

    email_contents = email_contents.replace("{word_contents}", word_content)

    if todays_announcement is not None:
        email_contents = email_contents.replace("{announcement_slot}", todays_announcement)
    else:
        email_contents = email_contents.replace("{announcement_slot}", "")

    return email_contents

def assemble_word_html_content(user_email, subscription, todays_words):
    print('assembling word content...')
    print('list subscription: ', subscription)

    word = todays_words[subscription.list_id]['word']
    print('selected word, ', word)
    if word is None:
        return ""
    else:
        # Select simplified or traditional character 
        if subscription.character_set == "simplified":
            selected_word = word["Simplified"]
        else:
            selected_word = word["Traditional"]

        # Hard coding list names and sentence URLs before list database refactor
        if subscription.list_name in ['HSK Level 1', 'HSK Level 2', 'HSK Level 3']:
            example_link = "https://www.yellowbridge.com/chinese/sentsearch.php?word=" + selected_word
        else:
            example_link = "https://fanyi.baidu.com/#zh/en/" + selected_word
        
        abs_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(abs_dir, 'word_template.html')) as fh:
            word_template = fh.read()

        # Hard coding HSK level before list database refactor
        hsk_level = subscription.list_name[-1]

        word_contents = word_template.replace("{word}", selected_word)
        word_contents = word_contents.replace("{pronunciation}", word["Pinyin"])
        word_contents = word_contents.replace("{definition}", word["Definition"])
        word_contents = word_contents.replace("{link}", example_link)
        word_contents = word_contents.replace("{list}", subscription.list_name)
        word_contents = word_contents.replace("{quiz_link}", "https://haohaotiantian.com/quiz?list=HSKLevel" + hsk_level + "&days=14&ques=10&char=" + subscription.character_set)
        word_contents = word_contents.replace("{signin_link}", "https://haohaotiantian.com/quiz?email=" + user_email)
        word_contents = word_contents.replace("{history_link}", "https://haohaotiantian.com/history?list=HSKLevel" + hsk_level + "&dates=30&char=" + subscription.character_set)

    return word_contents

def send_email(user, email_content):

    response = ses_client.send_email(
        Source = "Haohaotiantian <vocab@haohaotiantian.com>",
        Destination = {
            "ToAddresses" : [
            user.email_address
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
                    "Data": email_content
                }
            }
        }
    )

    return response