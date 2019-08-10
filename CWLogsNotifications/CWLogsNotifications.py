import os
import io
import json
import gzip
import boto3
import base64
from datetime import datetime

sns_client = boto3.client('sns')

def lambda_handler(event, context):
  
  log_json = decode_and_decompress_log(event)

  message = compose_message(log_json)

  response = sns_client.publish(
          TargetArn = os.environ['SUB_TOPIC_ARN'], 
          Message=json.dumps({'default': message}),
          MessageStructure='json'
      )

  print("SNS Response", response)

def decode_and_decompress_log(event):

  # Capture the CloudWatch log data
  outEvent = event['awslogs']['data']
  outEventDecoded = base64.b64decode(outEvent)
  
  # Decode and unzip the log data
  outEvent = gzip.decompress(outEventDecoded).decode('utf-8')
  
  log_json = json.loads(outEvent)

  return log_json

def compose_message(log_json):

  message_dict = {}

  # Function name
  message_dict["function name"] = log_json["logGroup"].replace("/aws/lambda/","")

  # Link
  date_timestamp = datetime.fromtimestamp(log_json['logEvents'][0]["timestamp"]/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
  message_dict["link"] = f"https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group={log_json['logGroup']};stream={log_json['logStream']};start={date_timestamp}"

  # Errors
  message_dict["errors list"] = []
  for error in log_json["logEvents"]:
    
    error_dict = {}

    date_timestamp = datetime.fromtimestamp(error["timestamp"]/1000)
    error_dict["time"] = date_timestamp.strftime('%Y-%m-%d %H:%M:%S')

    error_dict["error message"] = error["message"]

    message_dict["errors list"].append(error_dict)

  print(message_dict)

  return message_dict