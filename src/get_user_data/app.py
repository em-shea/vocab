import os
# import jwt
import json
import boto3
import urllib3
from boto3.dynamodb.conditions import Key

import sys
sys.path.insert(0, '/opt')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['DYNAMODB_TABLE_NAME'])
f"https://cognito-idp.{os.environ['AWS_REGION']}.amazonaws.com/{os.environ['USER_POOL_ID']}/.well-known/jwks.json"

# For a given user (requires sign-in), return their metadata, subscribed lists, and the past two weeks of quizzes and sentences
def lambda_handler(event, context):

    print(event['headers']['Authorization'])
    
    url = f"https://cognito-idp.{os.environ['AWS_REGION']}.amazonaws.com/{os.environ['USER_POOL_ID']}/.well-known/jwks.json"

    http = urllib3.PoolManager()
    response = http.request('GET', url)
    print(response.data)
    
    # response = get_user_data(body['user'])

    return

def get_user_data(user):

    response = table.query(
        KeyConditionExpression=Key('PK').eq(user)
    )
    print(response['Items'])
    return response['Items']