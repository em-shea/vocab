"""POST /testers: join the early testers."""
import json
from datetime import datetime, timezone

from join_testers.app import lambda_handler

OPEN = datetime(2026, 12, 1, tzinfo=timezone.utc)


def _event(uid='u1', body=None):
    return {'requestContext': {'authorizer': {'claims': {'sub': uid}}},
            'body': json.dumps(body) if body is not None else None}


def _user(table, uid='u1'):
    table.put_item(Item={'PK': f'USER#{uid}', 'SK': f'USER#{uid}', 'Email address': 'a@example.com'})


def test_join_sets_flag_since_and_answer(dynamodb_table):
    _user(dynamodb_table)
    with_patch(dynamodb_table)
    resp = lambda_handler(_event(body={'answer': '  Short daily quizzes  '}), None, now=OPEN)
    assert resp['statusCode'] == 200
    item = dynamodb_table.get_item(Key={'PK': 'USER#u1', 'SK': 'USER#u1'})['Item']
    assert item['Founding tester'] is True and item['Tester answer'] == 'Short daily quizzes'
    first = item['Tester since']
    lambda_handler(_event(), None, now=datetime(2026, 12, 5, tzinfo=timezone.utc))
    item = dynamodb_table.get_item(Key={'PK': 'USER#u1', 'SK': 'USER#u1'})['Item']
    assert item['Tester since'] == first and item['Tester answer'] == 'Short daily quizzes'
    assert item['Email address'] == 'a@example.com'


def test_closed_after_new_year(dynamodb_table):
    _user(dynamodb_table)
    with_patch(dynamodb_table)
    assert lambda_handler(_event(), None, now=datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc))['statusCode'] == 200
    assert lambda_handler(_event(), None, now=datetime(2027, 1, 1, tzinfo=timezone.utc))['statusCode'] == 403


def test_unknown_user_and_bad_body(dynamodb_table):
    with_patch(dynamodb_table)
    assert lambda_handler(_event('nobody'), None, now=OPEN)['statusCode'] == 404
    _user(dynamodb_table)
    assert lambda_handler(_event(body={'answer': 5}), None, now=OPEN)['statusCode'] == 400


def with_patch(table):
    import join_testers.app as app
    app.table = table
