import os
import jwt
import hmac
import boto3

cognito_client = boto3.client('cognito-idp', region_name=os.environ['AWS_REGION'])

def lambda_handler(event, context):

    response = event.get('response')
    request = event.get('request')
    session = request.get('session')

    expectedAnswer = request.get('privateChallengeParameters').get('answer')
    challengeAnswer = request.get('challengeAnswer')
    user_name = event.get('userName')

    if is_answer_valid(expectedAnswer, challengeAnswer, user_name):
        user_pool_id = event.get('userPoolId')

        attribute_update_response = cognito_client.admin_update_user_attributes(
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
    else:
        response.update({
            'answerCorrect': False
        })

    print(event)
    return event

def is_answer_valid(expected_answer, challenge_answer, user_name):

    if not expected_answer or not challenge_answer:
        return False

    # Binds the answer to the code issued for *this* challenge session.
    # Constant-time compare because this is a secret comparison.
    if not hmac.compare_digest(str(expected_answer), str(challenge_answer)):
        return False

    # The comparison above treats the code as an opaque string, so on its own it
    # would happily accept an expired code. Decode it so the exp claim set by
    # create_auth_challenge is actually enforced.
    try:
        claims = jwt.decode(challenge_answer, os.environ['OTP_SECRET_KEY'], algorithms=["HS256"])
    except jwt.InvalidTokenError as e:
        print('Rejected sign-in code: ', e)
        return False

    # A validly signed code issued for a different user must not sign this one in.
    if claims.get('u') != user_name:
        print('Rejected sign-in code: username does not match the code')
        return False

    return True