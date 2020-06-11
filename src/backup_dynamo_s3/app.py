import os
import json
import boto3
from datetime import datetime

dynamo_client = boto3.resource('dynamodb')
table = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])

s3 = boto3.resource('s3')
bucket = s3.Bucket(os.environ['BACKUPS_BUCKET_NAME'])

def lambda_handler(event, context):

    all_contacts_data = scan_contacts_table()

    data_rows = convert_to_rows(all_contacts_data)

    response = write_to_s3(data_rows)

def scan_contacts_table():

    # Loop through contacts in Dynamo
    results = table.scan(
        Select = "ALL_ATTRIBUTES"
    )

    all_contacts = results['Items']

    return all_contacts

def convert_to_rows(all_contacts_data):

    data_rows = []

    todays_date = format_date(datetime.today())

    # append today's date to each item as date of data pull
    for item in all_contacts_data:
        item['ReportingDate'] = todays_date
        data_rows.append(item)

    return data_rows

def write_to_s3(data_rows):
    
    todays_date = format_date(datetime.today())

    response = bucket.put_object(
        Body = json.dumps(data_rows).encode('UTF-8'),
        Key = f'{todays_date}.json'
    )

    return response

def format_date(date_object):

  formatted_date = date_object.strftime('%Y-%m-%d')

  return formatted_date