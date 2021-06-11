import os
import boto3

dynamo_client = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])

def lambda_handler(event, context):
    
    print(event)

    response = event.get('response')
    request = event.get('request')
    cognito_id = request.get('userAttributes').get('sub')
    user_email = request.get('userAttributes').get('email')

    # When a new user is signed up, add their info to the DynamoDB table
    create_contact_dynamo(response)
    
    print(event)
    return event

def create_contact_dynamo(response):

    table = dynamo_client.Table(os.environ['TABLE_NAME'])

    date = str(datetime.today().strftime('%-m/%d/%y'))

    sub_status = "subscribed"

    response = table.put_item(
        Item={
                'ListId': list_id,
                'SubscriberEmail' : email_address,
                'DateSubscribed': date,
                'Status': sub_status,
                'CharacterSet' : char_set
            }
        )