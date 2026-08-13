"""Tests for the authorized subscription endpoint (POST /subscriptions).

Identity comes from requestContext.authorizer.claims.sub, never from the request
body, so a caller can only change their own subscriptions.
"""
import json

from boto3.dynamodb.conditions import Key

from update_subscriptions.app import lambda_handler

LIST_ID = '1ebcad3f-5dfd-6bfe-bda4-acde48001122'   # HSK Level 1, public (seeded)
LIST_ID_2 = '1ebcad3f-adc0-6f42-b8b1-acde48001122'  # HSK Level 2, public (seeded)


def _event(sub, body):
    return {
        'resource': '/subscriptions', 'path': '/subscriptions', 'httpMethod': 'POST',
        'headers': {}, 'body': json.dumps(body), 'isBase64Encoded': False,
        'requestContext': {'authorizer': {'claims': {'sub': sub}}},
    }


def _subscription(list_id=LIST_ID, name='HSK Level 1', char='simplified'):
    return {'list_id': list_id, 'list_name': name, 'character_set': char}


def _seed_user(table, cognito_id, list_ids=(LIST_ID,)):
    table.put_item(Item={
        'PK': f'USER#{cognito_id}', 'SK': f'USER#{cognito_id}',
        'GSI1PK': 'USER', 'GSI1SK': f'USER#{cognito_id}',
        'Email address': f'{cognito_id}@test.com',
        'Character set preference': 'simplified',
        'Date created': '2026-01-01T00:00:00',
        'User alias': 'Not set', 'User alias pinyin': 'Not set', 'User alias emoji': 'Not set',
    })
    for list_id in list_ids:
        table.put_item(Item={
            'PK': f'USER#{cognito_id}', 'SK': f'LIST#{list_id}#SIMPLIFIED',
            'GSI1PK': 'USER', 'GSI1SK': f'USER#{cognito_id}#LIST#{list_id}#SIMPLIFIED',
            'List name': 'HSK Level 1', 'Status': 'subscribed',
            'Character set': 'simplified', 'Date subscribed': '2026-01-01T00:00:00',
        })


def _subs(table, cognito_id):
    items = table.query(KeyConditionExpression=Key('PK').eq(f'USER#{cognito_id}'))['Items']
    return {i['SK']: i['Status'] for i in items if i['SK'].startswith('LIST#')}


def test_adds_a_subscription(seeded_vocab_lists, dynamodb_table):
    _seed_user(dynamodb_table, 'user-1')

    response = lambda_handler(_event('user-1', {'subscriptions': [
        _subscription(), _subscription(LIST_ID_2, 'HSK Level 2'),
    ]}), '')

    assert response['statusCode'] == 200
    subs = _subs(dynamodb_table, 'user-1')
    assert subs[f'LIST#{LIST_ID}#SIMPLIFIED'] == 'subscribed'
    assert subs[f'LIST#{LIST_ID_2}#SIMPLIFIED'] == 'subscribed'


def test_removing_a_list_unsubscribes_it(seeded_vocab_lists, dynamodb_table):
    _seed_user(dynamodb_table, 'user-1', list_ids=(LIST_ID, LIST_ID_2))

    response = lambda_handler(_event('user-1', {'subscriptions': [_subscription()]}), '')

    assert response['statusCode'] == 200
    subs = _subs(dynamodb_table, 'user-1')
    assert subs[f'LIST#{LIST_ID}#SIMPLIFIED'] == 'subscribed'
    assert subs[f'LIST#{LIST_ID_2}#SIMPLIFIED'] == 'unsubscribed'


def test_empty_list_unsubscribes_everything(seeded_vocab_lists, dynamodb_table):
    _seed_user(dynamodb_table, 'user-1', list_ids=(LIST_ID, LIST_ID_2))

    response = lambda_handler(_event('user-1', {'subscriptions': []}), '')

    assert response['statusCode'] == 200
    assert set(_subs(dynamodb_table, 'user-1').values()) == {'unsubscribed'}


def test_identity_comes_from_claims_not_the_body(seeded_vocab_lists, dynamodb_table):
    """The whole point of the split: a cognito_id in the body must be ignored."""
    _seed_user(dynamodb_table, 'victim', list_ids=(LIST_ID,))
    _seed_user(dynamodb_table, 'attacker', list_ids=())

    # Authenticated as 'attacker', but claiming to be 'victim' in the body.
    response = lambda_handler(_event('attacker', {
        'cognito_id': 'victim',
        'subscriptions': [],
    }), '')

    assert response['statusCode'] == 200
    # The victim is untouched; only the authenticated caller's own subs changed.
    assert _subs(dynamodb_table, 'victim') == {f'LIST#{LIST_ID}#SIMPLIFIED': 'subscribed'}


def test_user_may_subscribe_to_their_own_private_list(seeded_vocab_lists, dynamodb_table):
    dynamodb_table.put_item(Item={
        'PK': 'LIST#mine', 'SK': 'METADATA', 'List name': 'My list',
        'Created by': 'USER#user-1', 'Visibility': 'private',
        'GSI1PK': 'LIST', 'GSI1SK': 'LIST#mine',
    })
    _seed_user(dynamodb_table, 'user-1', list_ids=())

    response = lambda_handler(_event('user-1', {
        'subscriptions': [_subscription('mine', 'My list')]
    }), '')

    assert response['statusCode'] == 200
    assert _subs(dynamodb_table, 'user-1')['LIST#mine#SIMPLIFIED'] == 'subscribed'


def test_user_may_not_subscribe_to_someone_elses_private_list(seeded_vocab_lists, dynamodb_table):
    dynamodb_table.put_item(Item={
        'PK': 'LIST#theirs', 'SK': 'METADATA', 'List name': 'Their list',
        'Created by': 'USER#someone-else', 'Visibility': 'private',
        'GSI1PK': 'LIST', 'GSI1SK': 'LIST#theirs',
    })
    _seed_user(dynamodb_table, 'user-1', list_ids=())

    response = lambda_handler(_event('user-1', {
        'subscriptions': [_subscription('theirs', 'Their list')]
    }), '')

    assert response['statusCode'] == 403
    assert _subs(dynamodb_table, 'user-1') == {}
