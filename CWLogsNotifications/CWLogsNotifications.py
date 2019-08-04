import os
import boto3

sns_client = boto3.client('sns')

def lambda_handler(event, context):

  message = "Notification Message"

  response = sns_client.publish(
          TargetArn = os.environ['SUB_TOPIC_ARN'], 
          Message=json.dumps({'default': message}),
          MessageStructure='json'
      )

  print("SNS Response", response)