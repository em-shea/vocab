import os
import io
import json
import gzip
import boto3
import base64

sns_client = boto3.client('sns')

def lambda_handler(event, context):
  
  #capture the CloudWatch log data
  outEvent = event['awslogs']['data']
  outEventDecoded = base64.b64decode(outEvent)
  
  #decode and unzip the log data
  outEvent = gzip.decompress(outEventDecoded).decode('utf-8')
  
  message = outEvent

  print(outEvent)

  response = sns_client.publish(
          TargetArn = os.environ['SUB_TOPIC_ARN'], 
          Message=json.dumps({'default': message}),
          MessageStructure='json'
      )

  print("SNS Response", response)