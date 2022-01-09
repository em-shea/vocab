import os
import boto3
from boto3.dynamodb.conditions import Key

import sys
sys.path.append('../tests/')

import format_user_data_service

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['DYNAMODB_TABLE_NAME'])

def get_all_users():

    dynamo_response = pull_all_users()
    grouped_user_and_subs = group_users_and_subs(dynamo_response)
    response = []
    for user_id, user in grouped_user_and_subs.items():
        response.append(format_user_data_service._format_user_data(user))

    return response

def pull_all_users():

    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('GSI1PK').eq('USER')
    )
    # print(response['Items'])
    return response['Items']

def group_users_and_subs(dynamo_response):

    grouped_user_and_subs = {}
    for item in dynamo_response:
        if item['PK'] not in grouped_user_and_subs:
            grouped_user_and_subs[item['PK']] = []
        grouped_user_and_subs[item['PK']].append(item)

    # print('grouped: ', grouped_user_and_subs)
    return grouped_user_and_subs