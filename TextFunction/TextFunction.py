import json
import boto3
import os
from botocore.vendored import requests

print("hello")

lambda_client = boto3.client('lambda')
sns_client = boto3.client('sns')

print("hello")

def lambda_handler(event, context):
    """Sends a daily random HSK vocab to SNS subscribers"""
    # Calls VocabRandomEntry, receives a single word's dictionary back
    hsk_level_arns = [
    {
      hsk_level: "1",
      topic_arn: os.environ['SNS_TOPIC_ARN1'],
    },
    {
      hsk_level: "2",
      topic_arn: os.environ['SNS_TOPIC_ARN2'],
    },
    {
      hsk_level: "3",
      topic_arn: os.environ['SNS_TOPIC_ARN3'],
    }
    {
      hsk_level: "4",
      topic_arn: os.environ['SNS_TOPIC_ARN4'],
    }
    {
      hsk_level: "5",
      topic_arn: os.environ['SNS_TOPIC_ARN5'],
    }
    {
      hsk_level: "6",
      topic_arn: os.environ['SNS_TOPIC_ARN6'],
    }
   ]
    
    for level in hsk_level_arns,
    
        invoke_response = lambda_client.invoke(
            FunctionName="VocabRandomEntry",
            InvocationType='RequestResponse'
        )
        response_json = invoke_response['Payload'].read()
        response_python = json.loads(response_json)
        word = response_python["body"]

        # Selects relevant parts of the word's dictionary and creates baidu URL
        message = "\n" + word["Word"] + "\n" + word["Pronunciation"] + "\n" + word["Definition"]
        baidu_link = "https://fanyi.baidu.com/#zh/en/" + word["Word"]

        # Publishes word, pronunciatino and definition to SNS
        response = sns_client.publish(
            TargetArn=os.environ['SNS_TOPIC_ARN'],
            Message=json.dumps({'default': message}),
            MessageStructure='json'
        )
        
        # Publishes baidu URL to SNS
        response = sns_client.publish(
            TargetArn=os.environ['SNS_TOPIC_ARN'],
            Message=json.dumps({'default': baidu_link}),
            MessageStructure='json'
        )