"""The daily push sender: who gets what, and what happens to dead devices."""
from unittest import mock

import pytest

from models import User, Subscription


def _user(user_id, subs, language='en'):
    return User(email_address='a@b.com', user_id=user_id, character_set_preference='simplified',
                user_alias='', user_alias_pinyin='', user_alias_emoji='', language_preference=language,
                subscriptions=[Subscription(list_name='HSK Level 1', unique_list_id=f'{l}#{c.upper()}', list_id=l,
                                            character_set=c, status=st, date_subscribed='') for l, c, st in subs],
                quizzes=[], sentences=[], writings=[])


WORDS = {
    'L1': [{'list_id': 'L1', 'date_sent': '2026-11-24', 'word': {'simplified': '爱护', 'traditional': '愛護', 'pinyin': 'ài hù', 'definition': 'to cherish; to take care of'}}],
    'L2': [{'list_id': 'L2', 'date_sent': '2026-11-24', 'word': {'simplified': '帮助', 'traditional': '幫助', 'pinyin': 'bāng zhù', 'definition': 'to help'}}],
}


@pytest.fixture
def app(dynamodb_table, idempotency_table, monkeypatch):
    monkeypatch.setenv('VAPID_KEY_PARAM', '/vocab/test/vapid-private-key')
    from send_daily_push import app as module
    return module


def test_message_has_a_line_per_list_in_the_users_set_and_language(app):
    user = _user('u1', [('L1', 'simplified', 'subscribed'), ('L2', 'traditional', 'subscribed')], language='cn')
    message = app.build_message(user, WORDS)
    assert message['title'] == '今日词语'
    assert message['body'] == '爱护 ài hù · to cherish\n幫助 bāng zhù · to help'
    assert message['url'].endswith('/profile')


def test_no_message_without_words_or_active_lists(app):
    assert app.build_message(_user('u1', [('L1', 'simplified', 'unsubscribed')]), WORDS) is None
    assert app.build_message(_user('u1', [('L9', 'simplified', 'subscribed')]), WORDS) is None


def _put_device(table, user, n):
    table.put_item(Item={'PK': f'USER#{user}', 'SK': f'PUSH#{n}', 'Endpoint': f'https://push.example.com/{n}',
                         'P256dh': 'k', 'Auth': 'a', 'GSI1PK': 'PUSH', 'GSI1SK': f'USER#{user}#PUSH#{n}'})


def test_sends_to_each_device_once_and_removes_dead_ones(app, dynamodb_table):
    _put_device(dynamodb_table, 'u1', 'live')
    _put_device(dynamodb_table, 'u1', 'dead')
    _put_device(dynamodb_table, 'u2', 'nolists')
    dynamodb_table.put_item(Item={'PK': 'USER#u1', 'SK': 'USER#u1', 'Email address': 'a@b.com'})
    users = [_user('u1', [('L1', 'simplified', 'subscribed')]), _user('u2', []), _user('u3', [('L1', 'simplified', 'subscribed')])]
    outcomes = {'https://push.example.com/live': 'sent', 'https://push.example.com/dead': 'gone'}
    event = {'detail': {'idempotency-key': 'k1'}, 'time': 't'}

    with mock.patch.object(app.review_word_service, 'get_review_words', return_value=WORDS), \
         mock.patch.object(app.user_service, 'get_all_users', return_value=users), \
         mock.patch.object(app, 'vapid_private_key', return_value='private'), \
         mock.patch.object(app, 'send', side_effect=lambda item, message, key: outcomes[item['Endpoint']]) as send:
        app.lambda_handler(event, '')
        assert send.call_count == 2  # u2 has no lists today; u3 has no device
        app.lambda_handler(event, '')  # same event again: nothing more is sent
        assert send.call_count == 2

    left = {i['SK'] for i in dynamodb_table.scan()['Items'] if i['PK'] == 'USER#u1'}
    assert left == {'USER#u1', 'PUSH#live'}


def test_remove_only_touches_push_items(app, dynamodb_table):
    dynamodb_table.put_item(Item={'PK': 'USER#u1', 'SK': 'LIST#L1#SIMPLIFIED'})
    app.remove({'PK': 'USER#u1', 'SK': 'LIST#L1#SIMPLIFIED'})
    assert len(dynamodb_table.scan()['Items']) == 1
