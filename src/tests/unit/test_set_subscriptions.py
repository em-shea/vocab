"""Tests for the public sign-up endpoint (POST /set_subs).

This endpoint has no Cognito authorizer, so the caller's identity arrives in the
request body and cannot be verified. It is therefore create-only: it may create a
user that does not exist, and must refuse to do anything to one that does. It
previously fell through to modifying an existing user's subscriptions, which meant
anyone knowing a subscriber's Cognito sub could add or remove their lists.
"""
import json

from boto3.dynamodb.conditions import Key

from set_subscriptions.app import lambda_handler

LIST_ID = '1ebcad3f-5dfd-6bfe-bda4-acde48001122'   # HSK Level 1, public (seeded)
LIST_ID_2 = '1ebcad3f-adc0-6f42-b8b1-acde48001122'  # HSK Level 2, public (seeded)


def _event(body):
    return {
        'resource': '/set_subs', 'path': '/set_subs', 'httpMethod': 'POST',
        'headers': {}, 'body': json.dumps(body), 'isBase64Encoded': False,
    }


def _body(cognito_id='user-1', email='me@test.com', subscriptions=None, list_id=LIST_ID):
    return {
        'cognito_id': cognito_id,
        'email': email,
        'character_set_preference': 'simplified',
        'subscriptions': subscriptions if subscriptions is not None else [
            {'list_id': list_id, 'list_name': 'HSK Level 1', 'character_set': 'simplified'}
        ],
    }


def _items(table, cognito_id):
    return table.query(
        KeyConditionExpression=Key('PK').eq(f'USER#{cognito_id}')
    )['Items']


def _private_list(table, list_id='private-list', owner='USER#someone-else'):
    table.put_item(Item={
        'PK': 'LIST#' + list_id, 'SK': 'METADATA',
        'List name': 'Private list', 'Created by': owner, 'Visibility': 'private',
        'GSI1PK': 'LIST', 'GSI1SK': 'LIST#' + list_id,
    })
    return list_id


def test_new_user_is_created_with_their_subscription(seeded_vocab_lists, dynamodb_table):
    response = lambda_handler(_event(_body()), '')

    assert response['statusCode'] == 200
    assert json.loads(response['body'])['success'] is True

    items = _items(dynamodb_table, 'user-1')
    assert {i['SK'] for i in items} == {
        'USER#user-1', f'LIST#{LIST_ID}#SIMPLIFIED',
    }
    subscription = next(i for i in items if i['SK'].startswith('LIST#'))
    assert subscription['Status'] == 'subscribed'


def test_multiple_initial_subscriptions_are_created(seeded_vocab_lists, dynamodb_table):
    body = _body(subscriptions=[
        {'list_id': LIST_ID, 'list_name': 'HSK Level 1', 'character_set': 'simplified'},
        {'list_id': LIST_ID_2, 'list_name': 'HSK Level 2', 'character_set': 'traditional'},
    ])

    response = lambda_handler(_event(body), '')

    assert response['statusCode'] == 200
    subs = [i for i in _items(dynamodb_table, 'user-1') if i['SK'].startswith('LIST#')]
    assert len(subs) == 2


def test_existing_user_is_rejected(seeded_vocab_lists, dynamodb_table):
    lambda_handler(_event(_body()), '')

    response = lambda_handler(_event(_body(email='attacker@test.com')), '')

    assert response['statusCode'] == 409
    assert json.loads(response['body'])['success'] is False


def test_existing_users_subscriptions_are_left_untouched(seeded_vocab_lists, dynamodb_table):
    """The security property: an unverifiable caller cannot alter a real user.

    Previously this handler swallowed the 'user exists' condition failure and went
    on to reconcile subscriptions - so passing an empty subscriptions list for
    somebody else's cognito_id unsubscribed them from everything.
    """
    lambda_handler(_event(_body()), '')
    before = _items(dynamodb_table, 'user-1')

    # An attacker who knows the sub tries to wipe the victim's subscriptions.
    response = lambda_handler(_event(_body(subscriptions=[])), '')

    assert response['statusCode'] == 409
    after = _items(dynamodb_table, 'user-1')
    assert after == before

    subscription = next(i for i in after if i['SK'].startswith('LIST#'))
    assert subscription['Status'] == 'subscribed'


def test_email_of_existing_user_cannot_be_overwritten(seeded_vocab_lists, dynamodb_table):
    lambda_handler(_event(_body(email='victim@test.com')), '')

    lambda_handler(_event(_body(email='attacker@test.com')), '')

    metadata = next(i for i in _items(dynamodb_table, 'user-1') if i['SK'].startswith('USER#'))
    assert metadata['Email address'] == 'victim@test.com'


def test_signing_up_to_a_private_list_is_refused(seeded_vocab_lists, dynamodb_table):
    list_id = _private_list(dynamodb_table)

    response = lambda_handler(_event(_body(list_id=list_id)), '')

    assert response['statusCode'] == 403
    # No user is created as a side effect of the rejected request.
    assert _items(dynamodb_table, 'user-1') == []


def test_signing_up_to_an_unknown_list_is_refused(seeded_vocab_lists, dynamodb_table):
    response = lambda_handler(_event(_body(list_id='no-such-list')), '')

    assert response['statusCode'] == 403
    assert _items(dynamodb_table, 'user-1') == []
