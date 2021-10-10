def lambda_handler(event, context):

    print(event)

    response = event.get('response')
    request = event.get('request')

    # User not found
    if request.get('userNotFound') is True:
        response.update({
            'issueTokens': False,
            'failAuthentication': True,
            'msg': "User does not exist"
        })
    # User is found
    else:
        session = request.get('session')
        
        # User has attempted to submit code at least once
        if len(session) != 0:

            # User is not going through custom auth flow
            if session[-1].get('challengeName') != 'CUSTOM_CHALLENGE':
                response.update({
                    'issueTokens': False,
                    'failAuthentication': True,
                    'msg': 'Custom auth flow (one-time code) required'
                })
            # User failed to provide the correct code after 3 attempts
            elif len(session) >= 3 and session[2].get('challengeResult') is False:
                response.update({
                    'issueTokens': False,
                    'failAuthentication': True,
                    'msg': 'Incorrect one-time code after 3 attempts'
                })
            # User entered the correct code!
            elif session[-1].get('challengeResult') is True:
                response.update({
                    'issueTokens': True,
                    'failAuthentication': False,
                })
            # User has entered incorrect OTP but has attempted less than 3 times
            else:
                response.update({
                    'issueTokens': False,
                    'failAuthentication': False,
                    'challengeName': 'CUSTOM_CHALLENGE'
                })

        # User has not entered OTP yet
        else:
            response.update({
                'issueTokens': False,
                'failAuthentication': False,
                'challengeName': 'CUSTOM_CHALLENGE'
            })

    print(event)
    return event