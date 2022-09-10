import os
import json
import boto3
import urllib.parse
from random import randint
from datetime import datetime
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

import user_service
import list_word_service
import vocab_list_service
import review_word_service

# region_name specified in order to mock in unit tests
ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION'])
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])
idempotency_table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['IDEMPOTENCY_TABLE'])

def lambda_handler(event, context):

    # check idempotency
    # put idempotency item
    # get words

    # Select a random word for each level
    # todays_words = get_daily_words()

    # If unable to store word in Dynamo, continue sending emails
    # try:
    #     # Write to Dynamo
    #     store_words(todays_words)
    # except Exception as e:
    #     print(e)

    print('event: ', event)
    idempotency_key = event['detail']['idempotency-key']
    time = event['time']
    consumer = "SendEmail"

    try:
        idempotency_response = check_idempotency_key(idempotency_key, consumer)
    except Exception as e:
        print(f"Error: Failed to check idempotency key - {idempotency_key, consumer}.")
        print(e)
        return e
    print("length:", len(idempotency_response))
    if len(idempotency_response) == 0:
        try:
            update_idempotency_table(idempotency_key, consumer, time)
        except Exception as e:
            print(f"Error: Failed to update idempotency key - {idempotency_key, consumer}.")
            print(e)
        
        try:
            todays_words = get_daily_words()
        except Exception as e:
            print(f"Error: Failed to retrieve todays words - {idempotency_key, consumer}.")
            print(e)
            return
        
        print('Send emails here')
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
    else:
        print(f'Email already sent for event with idempotency key: {idempotency_key}')

def check_idempotency_key(idempotency_key, consumer):

    response = idempotency_table.query(
        KeyConditionExpression=Key('IdempotencyKey').eq(idempotency_key) & Key('Consumer').eq(consumer)
    )
    print('check key response ', response)
    return response['Items']

def update_idempotency_table(idempotency_key, consumer, time):

    response = idempotency_table.put_item(
        Item = {
                'IdempotencyKey': idempotency_key,
                'Consumer': consumer,
                'Date': time
            }
        )
    print('update key response ', response)
    return response

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
    todays_words = review_word_service.get_review_words(list_id=None, date_range=0)
    print("words: ", dict(todays_words))
    return dict(todays_words)

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

    # Get first list user is subscribed to and use in unsub link
    url = os.environ['URL']
    email_contents = email_template.replace("{unsubscribe_link}", f"{url}/unsub?list=" + user.subscriptions[0].list_id + "&char=" + user.subscriptions[0].character_set + "&email=" + urllib.parse.quote_plus(user.email_address))
    email_contents = email_contents.replace("{signin_link}", f"{url}/signin?email=" + urllib.parse.quote_plus(user.email_address))

    email_contents = email_contents.replace("{word_contents}", word_content)

    if todays_announcement is not None:
        email_contents = email_contents.replace("{announcement_slot}", todays_announcement)
    else:
        email_contents = email_contents.replace("{announcement_slot}", "")

    return email_contents

def assemble_word_html_content(user_email, subscription, todays_words):
    print('assembling word content...')
    print('list subscription: ', subscription)

    url = os.environ['URL']
    word = todays_words[subscription.list_id][0]['word']
    print('selected word, ', word)
    if word is None:
        return ""
    else:
        # Select simplified or traditional character 
        if subscription.character_set == "simplified":
            selected_word = word["simplified"]
        else:
            selected_word = word["traditional"]

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
        word_contents = word_contents.replace("{pronunciation}", word["pinyin"])
        word_contents = word_contents.replace("{definition}", word["definition"])
        word_contents = word_contents.replace("{link}", example_link)
        word_contents = word_contents.replace("{list}", subscription.list_name)
        word_contents = word_contents.replace("{quiz_link}", f"{url}/quiz?list_id=" + subscription.list_id + "&date_range=30&ques=10&char=" + subscription.character_set)
        word_contents = word_contents.replace("{review_link}", f"{url}/review?list_id=" + subscription.list_id + "&date_range=30&char=" + subscription.character_set)

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