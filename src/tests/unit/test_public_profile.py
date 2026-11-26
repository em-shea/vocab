"""Opt-in public profiles, badges and the weekly leaderboard, against moto."""
import json
from datetime import date, timedelta

import public_profile_service as svc
from set_public_profile.app import lambda_handler as set_handler
from get_public_profile.app import lambda_handler as get_handler
from get_leaderboard.app import lambda_handler as board_handler

TODAY = date(2026, 11, 25)   # a Wednesday; the week starts Monday 2026-11-23


def _user(table, uid, alias='Not set', pinyin='Not set', **extra):
    item = {'PK': f'USER#{uid}', 'SK': f'USER#{uid}', 'Email address': f'{uid}@example.com',
            'GSI1PK': 'USER', 'GSI1SK': f'USER#{uid}', 'Date created': '2025-03-04T10:00:00',
            'User alias': alias, 'User alias pinyin': pinyin, 'User alias emoji': 'Not set'}
    item.update(extra)
    table.put_item(Item=item)


def _act(table, uid, day, kind='QUIZ', n=0, **extra):
    sk = f'DATE#{day.isoformat()}#{kind}#{kind.lower()}{n}'
    table.put_item(Item={'PK': f'USER#{uid}', 'SK': sk, **extra})


def _event(uid=None, body=None, handle=None):
    e = {'body': json.dumps(body) if body is not None else None,
         'queryStringParameters': {'handle': handle} if handle is not None else None}
    if uid:
        e['requestContext'] = {'authorizer': {'claims': {'sub': uid}}}
    return e


def _data(resp, status=200):
    assert resp['statusCode'] == status, resp
    return json.loads(resp['body'])['data']


def test_switch_on_creates_handle_and_keeps_it(dynamodb_table):
    _user(dynamodb_table, 'u1')
    on = _data(set_handler(_event('u1', {'public': True}), ''))
    assert on['public'] is True and len(on['handle']) == svc.HANDLE_LENGTH
    off = _data(set_handler(_event('u1', {'public': False}), ''))
    again = _data(set_handler(_event('u1', {'public': True}), ''))
    assert off['handle'] == on['handle'] == again['handle']
    item = dynamodb_table.get_item(Key={'PK': 'USER#u1', 'SK': 'USER#u1'})['Item']
    assert item['Public profile'] is True and item['Email address'] == 'u1@example.com'


def test_bad_body_and_unknown_user(dynamodb_table):
    assert set_handler(_event('u1', {'public': 'yes'}), '')['statusCode'] == 400
    assert set_handler(_event('nobody', {'public': True}), '')['statusCode'] == 404


def test_private_profile_is_404_and_never_shows_email(dynamodb_table):
    _user(dynamodb_table, 'u1', alias='李明', pinyin='Lǐ Míng')
    handle = _data(set_handler(_event('u1', {'public': True}), ''))['handle']
    body = get_handler(_event(handle=handle), '')['body']
    assert 'example.com' not in body
    profile = json.loads(body)['data']
    assert profile['name'] == '李明' and profile['joined'] == '2025-03'
    set_handler(_event('u1', {'public': False}), '')
    assert get_handler(_event(handle=handle), '')['statusCode'] == 404
    assert get_handler(_event(handle='nosuchone'), '')['statusCode'] == 404
    assert get_handler(_event(), '')['statusCode'] == 404


def test_badges():
    items = [{'SK': 'DATE#2026-11-20#QUIZ#a'},
             {'SK': 'DATE#2026-11-20#SENTENCE#b', 'Sentence': ''},       # empty: no badge
             {'SK': 'DATE#2026-11-21#WRITING#L#W'}]
    assert svc.badges({}, items, 7) == ['new_user', 'first_quiz', 'first_stroke_order']
    assert svc.badges({}, [], 100) == ['new_user']
    assert svc.badges({'Founding tester': True}, [], 0) == ['founding_tester', 'new_user']


def test_week_counts_monday_to_today_only():
    items = [{'SK': f'DATE#{d}#QUIZ#{i}'} for i, d in enumerate(
        ['2026-11-22', '2026-11-23', '2026-11-23', '2026-11-25'])]
    assert svc.week_activity(items, TODAY) == {'active_days': 2, 'actions': 3}


def test_leaderboard_ranks_public_profiles_only(dynamodb_table):
    for uid in ('a', 'b', 'c'):
        _user(dynamodb_table, uid)
    for uid in ('a', 'b'):
        svc.set_public(dynamodb_table, uid, True)
    # c is private but most active: must not appear
    for i in range(3):
        _act(dynamodb_table, 'c', TODAY - timedelta(days=i))
        _act(dynamodb_table, 'b', TODAY - timedelta(days=i))
    _act(dynamodb_table, 'a', TODAY)
    _act(dynamodb_table, 'a', TODAY, 'WRITING', 1)

    board = svc.get_leaderboard(dynamodb_table, TODAY)
    assert board['week_start'] == '2026-11-23'
    ranked = [(e['rank'], e['week']['active_days'], e['week']['actions']) for e in board['entries']]
    assert ranked == [(1, 3, 3), (2, 1, 2)]
    assert all('Cognito id' not in e and 'email' not in json.dumps(e) for e in board['entries'])


def test_leaderboard_handler(dynamodb_table):
    assert _data(board_handler({}, ''))['entries'] == []


def test_user_data_includes_own_public_settings(dynamodb_table):
    import user_service
    _user(dynamodb_table, 'u1')
    svc.set_public(dynamodb_table, 'u1', True)
    user = user_service.get_single_user('u1')
    assert user.public_profile is True and user.public_handle


def test_last_week_top_three(dynamodb_table):
    for uid in ('a', 'b', 'c', 'd'):
        _user(dynamodb_table, uid)
        svc.set_public(dynamodb_table, uid, True)
    last_monday = date(2026, 11, 16)
    for i in range(4):
        _act(dynamodb_table, 'a', last_monday + timedelta(days=i))
    for i in range(2):
        _act(dynamodb_table, 'b', last_monday + timedelta(days=i))
    _act(dynamodb_table, 'c', last_monday + timedelta(days=6))     # Sunday counts
    _act(dynamodb_table, 'd', TODAY)                                # this week only
    board = svc.get_leaderboard(dynamodb_table, TODAY)
    assert board['last_week_start'] == '2026-11-16'
    assert [(e['rank'], e['week']['active_days']) for e in board['last_week']] == [(1, 4), (2, 2), (3, 1)]
    assert all('_last_week' not in e for e in board['entries'] + board['last_week'])
