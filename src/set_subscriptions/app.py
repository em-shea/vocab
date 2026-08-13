import os
import json
import datetime

import subscription_service

# Public sign-up endpoint (POST /set_subs) - NO Cognito authorizer.
#
# The caller's identity arrives in the request body and cannot be verified, so this
# handler is deliberately create-only: it will create a user that does not yet exist
# and give it its initial subscriptions, and it refuses to do anything at all to a
# user that already exists. Changing an existing user's subscriptions requires the
# authorized POST /subscriptions endpoint, which reads the identity from verified
# token claims.
#
# This split exists because the endpoint previously trusted event_body['cognito_id']
# for both jobs, so anyone knowing a subscriber's Cognito sub could add or remove
# that person's subscriptions.


def _response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body)
    }


def lambda_handler(event, context):
    print(event)

    event_body = json.loads(event["body"])
    date = str(datetime.datetime.now().isoformat())

    cognito_id = event_body['cognito_id']
    subscriptions = event_body.get('subscriptions') or []

    # Anonymous callers may only subscribe to public lists
    unreadable = subscription_service.reject_unreadable_lists(subscriptions)
    if unreadable:
        print(f"Error: Sign-up requested non-public list(s) - {unreadable}.")
        return _response(403, {"success": False, "message": "Unknown or unavailable vocab list."})

    try:
        subscription_service.create_user(
            date, cognito_id, event_body['email'], event_body['character_set_preference']
        )
    except subscription_service.UserAlreadyExists:
        # Never fall through to modifying an existing user - that was the hole
        print(f"Sign-up attempted for an existing user - {cognito_id}.")
        return _response(409, {
            "success": False,
            "message": "User already exists. Sign in to change your subscriptions."
        })
    except Exception as e:
        print(f"Error: Failed to create user - {cognito_id}.")
        print(e)
        return _response(502, {"success": False})

    # A brand new user has no existing subscriptions, so this is a plain create -
    # no unsubscribe pass is needed or wanted here.
    for subscription in subscriptions:
        try:
            subscription_service.subscribe(date, cognito_id, subscription)
            print(f"sub {subscription['list_id']}, {subscription['character_set']}")
        except Exception as e:
            print(f"Error: Failed to subscribe new user - {cognito_id}, {subscription['list_id']}.")
            print(e)
            return _response(502, {"success": False})

    return _response(200, {"success": True})
