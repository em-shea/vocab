import os
import jwt
import time
import uuid
import boto3

ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION'])

# How long an emailed sign-in code stays valid.
OTP_TTL_SECONDS = 600

def lambda_handler(event, context):

    response = event.get('response')
    print(response)
    request = event.get('request')
    session = request.get('session')
    user_email = request.get('userAttributes').get('email')

    # Generate a sign-in code if this is the first attempt
    if (not session) or len(session) == 0:
        secret_login_code = generate_login_code(event)
        try:
            email_content = assemble_email_contents(secret_login_code)
            send_notification_email(user_email, email_content)
        except Exception as e:
            print(f"Error: Failed to send sign-in code - { user_email }.")
            print(e)
            return {
                'statusCode': 502,
                'headers': {
                    'Access-Control-Allow-Methods': 'POST,OPTIONS',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': '{"success" : false}'
            }
    # If this is a 2nd or 3rd attempt, reuse existing code
    # to give the user a chance if they accidentally miskeyed the code
    else: 
        previous_challenge = session[0]
        secret_login_code = previous_challenge.get('challengeMetadata')
    
    response.update({
        'privateChallengeParameters': {'answer': secret_login_code},
        'challengeMetadata': secret_login_code,
        # publicChallengeParameters is returned to the (unauthenticated) client that
        # started the auth flow, so it must NOT contain the secret login code — that
        # code is delivered only via email. Exposing it here would let any caller
        # obtain the code without access to the inbox, defeating passwordless auth.
        'publicChallengeParameters': {
            'email': user_email
        }
    })

    print(event)
    return event

def generate_login_code(event):

    # user_pool_id = event.get('userPoolId')
    username = event.get('userName')
    key = os.environ['OTP_SECRET_KEY']
    issued_at = int(time.time())

    # The payload was previously just {'u': username}, which is constant per user:
    # every sign-in produced the identical code, and with no exp claim that code
    # stayed valid forever. The nonce makes each code single-use in practice and
    # exp bounds its lifetime (enforced in verify_auth_challenge_response).
    encoded = jwt.encode({
        # 'user_pool_id': user_pool_id,
        'u' : username,
        'iat': issued_at,
        'exp': issued_at + OTP_TTL_SECONDS,
        'jti': str(uuid.uuid4())
        }, key, algorithm="HS256")

    # Deliberately not logged - this is the secret the user receives by email
    return encoded

def assemble_email_contents(secret_login_code):

    email_template = 'signin_code_template.html'
    login_link_staging = 'https://staging.haohaotiantian.com/verification?code=' + secret_login_code
    login_link_prod = 'https://haohaotiantian.com/verification?code=' + secret_login_code
    
    abs_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(abs_dir, email_template)) as fh:
        contents = fh.read()

    email_contents = contents.replace("{secret_login_code}", secret_login_code)
    if os.environ["STAGE"] == "staging":
        email_contents = email_contents.replace("{login_link}", login_link_staging)
    if os.environ["STAGE"] == "prod":
        email_contents = email_contents.replace("{login_link}", login_link_prod)

    return email_contents

def send_notification_email(user_email, email_content):

    subject_line = "Follow this link to sign in to Haohaotiantian."
    
    payload = ses_client.send_email(
        Source = "Haohaotiantian <signin@haohaotiantian.com>",
        Destination = {
            "ToAddresses" : [
            user_email
            ]
        },
        Message = {
            "Subject": {
                "Charset": "UTF-8",
                "Data": subject_line
                },
            "Body": {
                "Html": {
                    "Charset": "UTF-8",
                    "Data": email_content
                }
            }
        }
    )





