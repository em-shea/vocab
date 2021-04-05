# This Lambda function is invoked by the user pool when the user provides the answer to the challenge. 
# Its only job is to determine if that answer is correct.

# https://github.com/aws-samples/amazon-cognito-passwordless-email-auth/tree/master/cognito/lambda-triggers/verify-auth-challenge-response

def lambda_handler(event, context):
    return