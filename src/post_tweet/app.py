import os
import boto3

idempotency_table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['IDEMPOTENCY_TABLE'])

def lambda_handler(event, context):

    print('event: ', event)

    check_idempotency_key()

    return

def check_idempotency_key():

    # query