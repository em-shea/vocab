import os
import boto3

import vocab_list_service

import sys
sys.path.append('../tests/')

table = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION']).Table(os.environ['TABLE_NAME'])

# Subscription writes shared by the two entry points:
#
#   POST /set_subs      - public, sign-up only. Creates a user that does not yet
#                         exist and gives it its initial subscriptions. It cannot
#                         touch an existing user, because the caller's identity
#                         arrives in the request body and is unverifiable.
#   POST /subscriptions - Cognito-authorized. Changes an existing user's
#                         subscriptions, taking the identity from the verified
#                         token claims rather than the body.


class UserAlreadyExists(Exception):
    """Raised when sign-up is attempted for a user that already exists."""


def create_user(date, cognito_id, email_address, character_set_preference):
    """Create a user, or raise UserAlreadyExists.

    The condition expression is what makes the public sign-up path safe: a caller
    supplying someone else's cognito_id cannot overwrite that user's record.
    """
    try:
        return table.put_item(
            Item = {
                    'PK': "USER#" + cognito_id,
                    'SK': "USER#" + cognito_id,
                    'Email address': email_address,
                    'Date created': date,
                    'Last login': date,
                    'Character set preference': character_set_preference,
                    'User alias': "Not set",
                    'User alias pinyin': "Not set",
                    'User alias emoji': "Not set",
                    'GSI1PK': "USER",
                    'GSI1SK': "USER#" + cognito_id
                },
                ConditionExpression = "attribute_not_exists(PK)"
            )
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        raise UserAlreadyExists(cognito_id)


def subscribe(date, cognito_id, subscription):

    # PutItem will overwrite an existing item with the same key
    response = table.put_item(
        Item={
                'PK': "USER#" + cognito_id,
                'SK': "LIST#" + subscription['list_id'] + "#" + subscription['character_set'].upper(),
                'List name': subscription['list_name'],
                'Date subscribed': date,
                'Status': 'subscribed',
                'Character set': subscription['character_set'],
                'GSI1PK': "USER",
                'GSI1SK': "USER#" + cognito_id + "#LIST#" + subscription['list_id'] + "#" + subscription['character_set'].upper()
        }
    )

    return response


def unsubscribe(date, cognito_id, subscription):

    response = table.update_item(
        Key = {
            "PK": "USER#" + cognito_id,
            "SK": "LIST#" + subscription.list_id + "#" + subscription.character_set.upper()
        },
        UpdateExpression = "set #s = :status, #d = :date",
        ExpressionAttributeValues = {
            ":status": "unsubscribed",
            ":date": date
        },
        ExpressionAttributeNames = {
            "#s": "Status",
            "#d": "Date unsubscribed"
        },
        ReturnValues = "UPDATED_NEW"
        )

    return response


def readable_list_ids(cognito_id=None):
    """List ids this caller may subscribe to.

    Anonymous sign-up may only reach public lists. A signed-in user may also reach
    their own private lists. Without this check a caller could subscribe themselves
    to somebody else's private list and receive its words by email.
    """
    if cognito_id is None:
        lists = vocab_list_service.get_public_vocab_lists()
    else:
        lists = vocab_list_service.get_vocab_lists_for_user(cognito_id)
    return {l['list_id'] for l in lists}


def reject_unreadable_lists(subscriptions, cognito_id=None):
    """Return the ids in `subscriptions` the caller is not allowed to subscribe to."""
    allowed = readable_list_ids(cognito_id)
    return sorted({s['list_id'] for s in subscriptions} - allowed)


def reconcile_subscriptions(date, cognito_id, desired_subscriptions, existing_subscriptions):
    """Make the user's subscriptions match `desired_subscriptions` exactly.

    Subscribes everything desired (idempotent - PutItem overwrites), then
    unsubscribes anything currently subscribed that is not in the desired set.
    """
    desired_unique_ids = [
        s['list_id'] + "#" + s['character_set'].upper() for s in desired_subscriptions
    ]

    for subscription in desired_subscriptions:
        subscribe(date, cognito_id, subscription)

    for existing in existing_subscriptions:
        if existing.unique_list_id not in desired_unique_ids and existing.status == "subscribed":
            unsubscribe(date, cognito_id, existing)
