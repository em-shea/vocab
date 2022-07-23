import os
import json
import boto3
from datetime import datetime

s3 = boto3.resource('s3')
bucket = s3.Bucket(os.environ['BACKUPS_BUCKET_NAME'])

# region_name specified in order to mock in unit tests
dynamo_client = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):

    all_contacts_data = scan_contacts_table()

    todays_date = format_date(datetime.today())

    data_rows = convert_to_rows(all_contacts_data, todays_date)

    response = write_to_s3(data_rows, todays_date)

def scan_contacts_table():

    # Loop through contacts in Dynamo
    response = table.scan()
    all_contacts = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        all_contacts.extend(response['Items'])

    return all_contacts

def convert_to_rows(all_contacts_data, todays_date):

    data_rows = []

    # Append today's date to each item as date of data pull
    # Standardizing date formats since QuickSight can't handle mixed date formats
    for item in all_contacts_data:
        item['Reporting date'] = todays_date
        if 'Date subscribed' in item:
            item['Date subscribed'] = datetime.fromisoformat(item['Date subscribed']).strftime('%Y-%m-%dT%H:%M:%S') # yyyy-MM-dd'T'HH:mm:ss
        if 'Date unsubscribed' in item:
            item['Date unsubscribed'] = datetime.fromisoformat(item['Date unsubscribed']).strftime('%Y-%m-%dT%H:%M:%S') # yyyy-MM-dd'T'HH:mm:ss
        if 'Date created' in item:
            item['Date created'] = datetime.fromisoformat(item['Date created']).strftime('%Y-%m-%dT%H:%M:%S') # yyyy-MM-dd'T'HH:mm:ss
        data_rows.append(item)

    return data_rows

def write_to_s3(data_rows, todays_date):
    
    response = bucket.put_object(
        Body = json.dumps(data_rows).encode('UTF-8'),
        Key = f'{todays_date}.json'
    )

    return response

def format_date(date_object):

    formatted_date = date_object.strftime('%Y-%m-%d')

    return formatted_date