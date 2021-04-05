# This function auto-confirms users and their email addresses during sign-up

# https://github.com/aws-samples/amazon-cognito-passwordless-email-auth/blob/master/cognito/lambda-triggers/pre-sign-up/pre-sign-up.ts

# import { PreSignUpTriggerHandler } from 'aws-lambda';

# export const handler: PreSignUpTriggerHandler = async event => {
#     event.response.autoConfirmUser = true;
#     return event;
# };

def lambda_handler(event, context):
    
    print(response)

    response = event.get('response')
    response.update({
        'autoConfirmUser': True
    })
    
    return event