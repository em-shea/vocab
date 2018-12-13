import json
import boto3
import os
from botocore.vendored import requests

print("hello")

lambda_client = boto3.client('lambda')
sns_client = boto3.client('sns')

print("hello")

def lambda_handler(event, context):
    """Calls VocabRandomEntry function"""
    invoke_response = lambda_client.invoke(
        FunctionName="VocabRandomEntry",
        InvocationType='RequestResponse'
    )
    response_json = invoke_response['Payload'].read()
    response_python = json.loads(response_json)
    word = response_python["body"]

    message = "\n" + word["Word"] + "\n" + word["Pronunciation"] + "\n" + word["Definition"]
    baidu_link = "https://fanyi.baidu.com/#zh/en/" + word["Word"]

    response = sns_client.publish(
        TargetArn='arn:aws:sns:us-east-1:789896561553:Vocab',
        Message=json.dumps({'default': message}),
        MessageStructure='json'
    )
    
    response = sns_client.publish(
        TargetArn='arn:aws:sns:us-east-1:789896561553:Vocab',
        Message=json.dumps({'default': baidu_link}),
        MessageStructure='json'
    )