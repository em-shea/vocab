def lambda_handler(event, context):

    print(event)

    response = event.get('response')
    request = event.get('request')
    session = request.get('session')

    if len(session) != 0:
        print('at least one attempt')
    elif len(session) == 0:
        print('no attempts yet')
        response.update({
            'issueTokens': False,
            'failAuthentication': False,
            'challengeName': 'CUSTOM_CHALLENGE'
        })


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

    return event