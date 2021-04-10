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

        # User has not entered OTP yet, or has entered incorrect OTP but has attempted less than 3 times
        else:
            response.update({
                'issueTokens': False,
                'failAuthentication': False,
                'challengeName': 'CUSTOM_CHALLENGE'
            })


    # If user not found, fail auth
    # If auth flow is not custom challenge, fail auth
    # If user attempts 3 times with the wrong OTP, fail auth
    # Correct custom auth flow and OTP, succeed auth
    # User did not provide the right answer yet (under 3 attempts), present auth challenge
    


    # if len(session) != 0:

    #     current_session = len(session) - 1

    #     # If user not found, fail auth
    #     if request.get('userNotFound') is True:
    #         response.update({
    #             'issueTokens': False,
    #             'failAuthentication': True,+
    #             'msg': "User does not exist"
    #         })
    #     # If user does not go through custom auth challenge flow, fail auth
    #     elif session[current_session].get('challengeName') != 'CUSTOM_CHALLENGE':
    #         response.update({
    #             'issueTokens': False,
    #             'failAuthentication': True,
    #             'msg': 'User must use custom challenge to sign in'
    #         })
    #     # If user attempts 3 times with the wrong OTP, fail auth
    #     elif len(session) >= 3 and session[2].get('challengeResult') is False:
    #         response.update({
    #             'issueTokens': False,
    #             'failAuthentication': True,
    #             'msg': 'Incorrect OTP after 3 attempts'
    #         })
    #     # Correct custom auth flow and OTP, succeed auth
    #     elif len(session) >0 and session[current_session].get('challengeName') == 'CUSTOM_CHALLENGE' and session[current_session].get('challengeResult') is True:
    #         response.update({
    #             'issueTokens': True,
    #             'failAuthentication': False
    #         })
    # # User did not provide the right answer yet (under 3 attempts), present auth challenge
    # else:
    #     response.update({
    #         'issueTokens': False,
    #         'failAuthentication': False,
    #         'challengeName': 'CUSTOM_CHALLENGE'
    #     })

    print(event)
    return event