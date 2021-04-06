# This Lambda function is invoked by the user pool when the user provides the answer to the challenge. 
# Its only job is to determine if that answer is correct.

# https://github.com/aws-samples/amazon-cognito-passwordless-email-auth/tree/master/cognito/lambda-triggers/verify-auth-challenge-response

import os
import jwt
import boto3

cognito_client = boto3.client('cognito-identity', region_name=os.environ['AWS_REGION'])

def lambda_handler(event, context):

    response = event.get('response')
    request = event.get('request')
    session = request.get('session')

    expectedAnswer = request.get('privateChallengeParameters').get('answer') 
    challengeAnswer = request.get('challengeAnswer')

    if expectedAnswer == challengeAnswer:
        user_pool_id = event.get('userPoolId')
        user_name = event.get('userName')

        result = cognito_client.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=user_name,
            UserAttributes=[
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                }
            ]
        )
        response.update({
            'answerCorrect': True
        })
    else {
        response.update({
            'answerCorrect': False
        })
    }

    return event