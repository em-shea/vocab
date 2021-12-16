import os
import json
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# TODO: Add cognito id to unsub URL params

import random_word_service

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

    # Scan the contacts table for a list of all contacts
    users_and_subscriptions = get_users_and_subscriptions()

    users_and_subscriptions_grouped = process_users_and_subscriptions(users_and_subscriptions)

    email_counter = 0
    for user_id, user in users_and_subscriptions_grouped.items():
        # print('loop through users')
        if len(user['lists'])>0:
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

    todays_words = {}

    # Hard coding list names for now before refactoring list database
    list_names = ['HSK Level 1', 'HSK Level 2', 'HSK Level 3', 'HSK Level 4', 'HSK Level 5', 'HSK Level 6']

    # Loop through all lists and select word
    for list in list_names:
        level = str(list_names.index(list)+1)
        try:
            word = random_word_service.select_random_word(level)
            todays_words[list] = word
        except Exception as e:
            # Appending None to the list as a placeholder for the level's word. Emails will not send for this level.
            todays_words[list] = None
            print(e)

    return todays_words

def store_words(todays_words):

    for list_name, word in todays_words.items():
        date = str(datetime.today().strftime('%Y-%m-%d'))

        # Write each word to Dynamo word history table
        response = word_history_table.put_item(
            Item={
                    'ListId': list_name.replace(" ", ""),
                    'Date': date,
                    'Word': word,
                }
            )
    print(response)

def get_users_and_subscriptions():

    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq('USER')
    )
    # print(response['Items'])
    return response['Items']

def process_users_and_subscriptions(users_and_subscriptions):

    users_and_subscriptions_grouped = {}
    # users_and_subscriptions_grouped = {
    #     user_id: {
    #         'user_data': {user metadata},
    #         'lists': [
    #             {sub metadata}
    #         ]
    #     }
    # }

    # Loop through all users and subs
    for item in users_and_subscriptions:
        # If user is not yet in the grouped dict, add a new dict for the user
        if item['PK'] not in users_and_subscriptions_grouped:
            users_and_subscriptions_grouped[item['PK']] = {'user_data': None, 'lists': []}
        
        # If Dynamo item is a user, add user metadata to the user's dict
        if 'Email address' in item:
            print('user metadata', item['Email address'])
            users_and_subscriptions_grouped[item['PK']]['user_data'] = item

        # If Dynamo item is a list subscription and the status is subscribed, add the list to the user's dict
        if 'List name' in item:
            print('user list', item['List name'])
            if item['Status'] == 'subscribed':
                users_and_subscriptions_grouped[item['PK']]['lists'].append(item)
                print('subscribed')
            else:
                print('unsubscribed')

    print(users_and_subscriptions_grouped)

    return users_and_subscriptions_grouped

def assemble_html_content(user, todays_words, todays_announcement):

    # Appends multiple words into the same email
    # TODO: Order the lists in some way?
    word_content = ""
    for list in user['lists']:
        word_content = word_content + assemble_word_html_content(user['user_data']['Email address'], list, todays_words)

    # Open HTML template file
    # To run unit tests, we need to specify an absolute file path
    abs_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(abs_dir, 'email_template.html')) as fh:
        email_template = fh.read()

    # Hard coding HSK level before list database refactor
    # Get first list user is subscribed to and use in unsub link
    hsk_level = user['lists'][0]['List name'][-1]
    char_set = user['lists'][0]['Character set']
    email_contents = email_template.replace("{unsubscribe_link}", "https://haohaotiantian.com/unsub?level=" + hsk_level + "&email=" + user['user_data']['Email address'] + "&char=" + char_set)
    
    email_contents = email_contents.replace("{word_contents}", word_content)

    if todays_announcement is not None:
        email_contents = email_contents.replace("{announcement_slot}", todays_announcement)
    else:
        email_contents = email_contents.replace("{announcement_slot}", "")

    return email_contents

def assemble_word_html_content(user_email, list, todays_words):

    word = todays_words[list['List name']]
    if word is None:
        return ""
    else:
        # Select simplified or traditional character 
        if list['Character set'] == "simplified":
            selected_word = word["Word"]
        else:
            selected_word = word["Word-Traditional"]
        
        # Hard coding list names and sentence URLs before list database refactor
        if list['List name'] in ['HSK Level 1', 'HSK Level 2', 'HSK Level 3']:
            example_link = "https://www.yellowbridge.com/chinese/sentsearch.php?word=" + selected_word
        else:
            example_link = "https://fanyi.baidu.com/#zh/en/" + selected_word
        
        abs_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(abs_dir, 'word_template.html')) as fh:
            word_template = fh.read()

        # Hard coding HSK level before list database refactor
        hsk_level = list['List name'][-1]

        word_contents = word_template.replace("{word}", selected_word)
        word_contents = word_contents.replace("{pronunciation}", word["Pronunciation"])
        word_contents = word_contents.replace("{definition}", word["Definition"])
        word_contents = word_contents.replace("{link}", example_link)
        word_contents = word_contents.replace("{list}", list['List name'])
        word_contents = word_contents.replace("{quiz_link}", "https://haohaotiantian.com/quiz?list=HSKLevel" + hsk_level + "&days=14&ques=10&char=" + list['Character set'])
        word_contents = word_contents.replace("{signin_link}", "https://haohaotiantian.com/quiz?email=" + user_email)
        word_contents = word_contents.replace("{history_link}", "https://haohaotiantian.com/history?list=HSKLevel" + hsk_level + "&dates=30&char=" + list['Character set'])

    return word_contents

def send_email(user, email_content):

    response = ses_client.send_email(
        Source = "Haohaotiantian <vocab@haohaotiantian.com>",
        Destination = {
            "ToAddresses" : [
            user['user_data']['Email address']
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