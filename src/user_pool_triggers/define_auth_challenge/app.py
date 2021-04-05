def lambda_handler(event, context):

    response = event.get('response')
    print(response)
    request = event.get('request')
    session = request.get('session')

    current_session = len(session) - 1

    # If user does not go through custom auth challenge flow, fail auth
    if current_session.get('challengeName') !=== 'CUSTOM_CHALLENGE':
        response.update({
            'issueTokens': False,
            'failAuthentication': True,
            'msg': 'User must use custom challenge to sign in'
        })
    # If user attemps 3 times with the wrong OTP, fail auth
    elif len(session) >= 3 and session[2].get('challengeResult') is False:
        response.update({
            'issueTokens': False,
            'failAuthentication': True,
            'msg': 'Incorrect OTP after 3 attempts'
        })
    # Correct custom auth flow and OTP, succeed auth
    elif current_session.get('challengeName') === 'CUSTOM_CHALLENGE' and current_session.get('challengeResult') is True:
        response.update({
            'issueTokens': False,
            'failAuthentication': True
        })
    # Wrong OTP but less than 3 attempts, present auth challenge
    else:
        response.update({
            'issueTokens': False,
            'failAuthentication': False,
            'challengeName': 'CUSTOM_CHALLENGE'
        })

    return event