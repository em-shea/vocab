import boto3

def lambda_handler(event, context):
  
  # hsk_level = event["queryStringParameters"]['hsk_level']
  email_address = event["queryStringParameters"]['email']

  # Add dictionary with SNS topic ARNs by level

  MY_SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:789896561553:vocab-Level1Topic-13PMNB2U5WC84'
  sns_client = boto3.client('sns')
  sns_client.subscribe(
      TopicArn = MY_SNS_TOPIC_ARN,
      Protocol = 'email',
      Endpoint = email_address
  )

  return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            # 'Access-Control-Allow-Origin': os.environ['DomainName'],
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"success" : true}'
    }