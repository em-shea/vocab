# This Lambda function is invoked, based on the instruction of the “Define Auth Challenge” trigger, 
# to create a unique challenge for the user. 
# We’ll use it to generate a one-time login code and mail it to the user.

# https://github.com/aws-samples/amazon-cognito-passwordless-email-auth/blob/master/cognito/lambda-triggers/create-auth-challenge/create-auth-challenge.ts

def lambda_handler(event, context):
    return