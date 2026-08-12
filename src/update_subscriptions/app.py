import json
import datetime

import api_response
import user_service
import subscription_service

# Authorized subscription changes (POST /subscriptions).
#
# The identity comes from requestContext.authorizer.claims.sub - the same pattern
# every other authorized handler uses - so a caller can only ever change their own
# subscriptions. Any cognito_id in the request body is ignored.


def lambda_handler(event, context):
    print(event)

    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    event_body = json.loads(event["body"])
    date = str(datetime.datetime.now().isoformat())

    desired_subscriptions = event_body.get('subscriptions') or []

    # A signed-in user may subscribe to public lists and to their own private lists
    unreadable = subscription_service.reject_unreadable_lists(desired_subscriptions, cognito_id)
    if unreadable:
        print(f"Error: {cognito_id} requested list(s) they cannot read - {unreadable}.")
        return api_response.response(403, "Unknown or unavailable vocab list.")

    try:
        user = user_service.get_single_user(cognito_id)
    except Exception as e:
        print(f"Error: Failed to load user - {cognito_id}.")
        print(e)
        return api_response.response(502, "Failed to update subscriptions.")

    try:
        subscription_service.reconcile_subscriptions(
            date, cognito_id, desired_subscriptions, user.subscriptions
        )
    except Exception as e:
        print(f"Error: Failed to update subscriptions - {cognito_id}.")
        print(e)
        return api_response.response(502, "Failed to update subscriptions.")

    return api_response.response(200, "Successfully updated subscriptions.")
