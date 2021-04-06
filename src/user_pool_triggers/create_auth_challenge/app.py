# This function creates and sends a sign-in code to the user
import jwt
import boto3

ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION'])

def lambda_handler(event, context):

    response = event.get('response')
    print(response)
    request = event.get('request')
    user_email = request.get('userAttributes').get('email')

    # Generate a sign-in code if this is the first attempt
    if (not session) or len(session) === 0:
        secret_login_code = generate_login_code(event)
        try:
            send_notification_email(user_email, secret_login_code)
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
        'privateChallengeParamters': {'answer': secret_login_code},
        'challengeMetadata': secret_login_code,
        'publicChallengeParamters': {
            'answer': secret_login_code
        }
    })

    return event

def generate_login_code(event):

    user_pool_id = event.get('userPoolId')
    username = event.get('userName')
    key = '123456789'

    encoded = jwt.encode({ 
        'user_pool_id': user_pool_id,
        'username' : username 
        }, key, algorithm="HS256")
    
    print(encoded)
    return encoded

def send_notification_email(user_email, secret_login_code):

    subject_line = "Please follow this link or enter this sign-in code."
    
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
                    "Data": secret_login_code
                }
            }
        }
    )





