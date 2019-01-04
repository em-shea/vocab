import json
import boto3
import os
import time
from botocore.vendored import requests

lambda_client = boto3.client('lambda')
sns_client = boto3.client('sns')

def get_random(any_level):
    invoke_response = lambda_client.invoke(
        FunctionName="VocabRandomEntry",
        InvocationType='RequestResponse',       
        Payload=json.dumps({
            "hsk_level": any_level
        })
    )

    response_json = invoke_response['Payload'].read()
    response_python = json.loads(response_json)
    word = response_python["body"]
    return word

def lambda_handler(event, context):
    """Sends a daily random HSK vocab to SNS subscribers"""
    # Calls VocabRandomEntry, receives a single word's dictionary back
    hsk_level_arns = [{
        "hsk_level": "1",
        "topic_arn": os.environ['SNS_TOPIC_ARN1'],
    },{
        "hsk_level": "2",
        "topic_arn": os.environ['SNS_TOPIC_ARN2'],
    },{
        "hsk_level": "3",
        "topic_arn": os.environ['SNS_TOPIC_ARN3'],
    },{
        "hsk_level": "4",
        "topic_arn": os.environ['SNS_TOPIC_ARN4'],
    },{
        "hsk_level": "5",
        "topic_arn": os.environ['SNS_TOPIC_ARN5'],
    },{
        "hsk_level": "6",
        "topic_arn": os.environ['SNS_TOPIC_ARN6'],
    }]
    
    for level_dict in hsk_level_arns:
        level = level_dict["hsk_level"]
        word = get_random(level)
        num_level = int(level)

        message = ("HSK Level: " + level_dict["hsk_level"] + "\n" + word["Word"] + 
            "\n" + word["Pronunciation"] + "\n" + word["Definition"]) 
        
        if num_level in range(1,4):
            url = "\n \n" + "https://www.yellowbridge.com/chinese/charsearch.php?zi=" + word["Word"]
  
        else: 
            url = "\n \n" + "https://fanyi.baidu.com/#zh/en/" + word["Word"]

        complete_message = message + url

        # Publishes word, pronunciation and definition to SNS
        response = sns_client.publish(
            TargetArn=level_dict["topic_arn"],
            Message=json.dumps({'default': complete_message}),
            MessageStructure='json'
        )
    

        