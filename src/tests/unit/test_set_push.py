"""POST /push: one device's daily word notifications on or off, against a fake table."""
import json

from boto3.dynamodb.conditions import Key

from set_push.app import lambda_handler, push_key

SUB = {'endpoint': 'https://fcm.googleapis.com/fcm/send/abc123', 'keys': {'p256dh': 'BPkey', 'auth': 'authsecret'}}


def _event(body, sub='user-1'):
    return {'body': json.dumps(body) if not isinstance(body, str) else body,
            'requestContext': {'authorizer': {'claims': {'sub': sub}}}}


def _items(table, user='user-1'):
    return table.query(KeyConditionExpression=Key('PK').eq(f'USER#{user}'))['Items']


def test_subscribing_saves_one_item_per_device(dynamodb_table):
    assert lambda_handler(_event({'action': 'subscribe', 'subscription': SUB}), '')['statusCode'] == 200
    assert lambda_handler(_event({'action': 'subscribe', 'subscription': SUB}), '')['statusCode'] == 200
    items = _items(dynamodb_table)
    assert len(items) == 1
    item = items[0]
    assert item['SK'] == push_key(SUB['endpoint']) and item['SK'].startswith('PUSH#')
    assert item['Endpoint'] == SUB['endpoint'] and item['P256dh'] == 'BPkey' and item['Auth'] == 'authsecret'
    assert item['GSI1PK'] == 'PUSH'


def test_unsubscribing_removes_only_that_devices_item(dynamodb_table):
    dynamodb_table.put_item(Item={'PK': 'USER#user-1', 'SK': 'USER#user-1', 'Email address': 'a@b.com'})
    dynamodb_table.put_item(Item={'PK': 'USER#user-1', 'SK': 'LIST#L1#SIMPLIFIED', 'Status': 'subscribed'})
    other = {**SUB, 'endpoint': 'https://push.example.com/other'}
    for s in (SUB, other):
        lambda_handler(_event({'action': 'subscribe', 'subscription': s}), '')

    assert lambda_handler(_event({'action': 'unsubscribe', 'subscription': {'endpoint': SUB['endpoint']}}), '')['statusCode'] == 200

    sks = sorted(i['SK'] for i in _items(dynamodb_table))
    assert sks == sorted(['USER#user-1', 'LIST#L1#SIMPLIFIED', push_key(other['endpoint'])])


def test_bad_requests_are_400_and_change_nothing(dynamodb_table):
    bad = [
        'not json',
        {'action': 'maybe', 'subscription': SUB},
        {'action': 'subscribe', 'subscription': {**SUB, 'endpoint': 'http://insecure.example.com'}},
        {'action': 'subscribe', 'subscription': {'endpoint': SUB['endpoint'], 'keys': {}}},
    ]
    for body in bad:
        assert lambda_handler(_event(body), '')['statusCode'] == 400, body
    assert _items(dynamodb_table) == []
