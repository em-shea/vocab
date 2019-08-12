import os
import io
import csv
import boto3

def get_contact_level_list():
  s3_client = boto3.client('s3')

  # Read file from S3
  csv_file = s3_client.get_object(Bucket=os.environ['LISTS_BUCKET_NAME'], Key=os.environ['LISTS_BUCKET_KEY'])
  csv_response = csv_file['Body'].read()
  stream = io.StringIO(csv_response.decode("utf-8"))
  reader = csv.DictReader(stream)

  # Create an empty list that will hold the contact lists
  contact_level_lists = []

  # Filter contact lists for the correct stage
  for row in reader: 
      if row['stage'] == os.environ['STAGE']:
          contact_level_lists.append(dict(row))

  return contact_level_lists