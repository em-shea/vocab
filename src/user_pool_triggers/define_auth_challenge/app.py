def lambda_handler(event, context):

    print(event)

    response = event.get('response')
    request = event.get('request')
    session = request.get('session')


    current_session = len(session) - 1

    # If user not found, fail auth
    if request.get('userNotFound') is True:
        response.update({
            'issueTokens': False,
            'failAuthentication': True,+
            'msg': "User does not exist"
        }) elif session[current_session].get('challengeName') != 'CUSTOM_CHALLENGE':
        # If user does not go through custom auth challenge flow, fail auth
        response.update({
            'issueTokens': False,
            'failAuthentication': True,
            'msg': 'User must use custom challenge to sign in'
        }) elif len(session) >= 3 and session[2].get('challengeResult') is False:
        # If user attempts 3 times with the wrong OTP, fail auth
        response.update({
            'issueTokens': False,
            'failAuthentication': True,
            'msg': 'Incorrect OTP after 3 attempts'
        }) elif len(session) >0 and session[current_session].get('challengeName') == 'CUSTOM_CHALLENGE' and session[current_session].get('challengeResult') is True:
        # Correct custom auth flow and OTP, succeed auth
        response.update({
            'issueTokens': True,
            'failAuthentication': False
        }) else:
        # User did not provide the right answer yet (under 3 attempts), present auth challenge
        response.update({
            'issueTokens': False,
            'failAuthentication': False,
            'challengeName': 'CUSTOM_CHALLENGE'
        })

    return event