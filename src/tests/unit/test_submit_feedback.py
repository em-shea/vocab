"""POST /feedback: a signed-in user's message is emailed to nihao@ with Reply-To set to them."""
import json
import email
from unittest import mock

from submit_feedback import app
from models import User


def _event(body, sub='user-1'):
    return {'body': json.dumps(body) if not isinstance(body, str) else body,
            'requestContext': {'authorizer': {'claims': {'sub': sub}}}}


def _user(alias='小安'):
    return User(email_address='learner@example.com', user_id='user-1', character_set_preference='simplified',
                user_alias=alias, user_alias_pinyin='', user_alias_emoji='Not set',
                subscriptions=[], quizzes=[], sentences=[])


def _send(body, user=None):
    with mock.patch.object(app.user_service, 'get_single_user', return_value=user or _user()), \
         mock.patch.object(app, 'ses_client') as ses:
        result = app.lambda_handler(_event(body), None)
    return result, ses


def test_sends_to_inbox_with_reply_to_the_user():
    result, ses = _send({'message': 'The stroke order page <b>froze</b>.', 'page': '/write'})
    assert result['statusCode'] == 200
    assert ses.send_raw_email.call_count == 2
    kwargs = ses.send_raw_email.call_args_list[0].kwargs
    assert kwargs['Destinations'] == ['nihao@haohaotiantian.com']
    msg = email.message_from_bytes(kwargs['RawMessage']['Data'])
    assert msg['Reply-To'] == 'learner@example.com'
    assert '小安' in str(email.header.make_header(email.header.decode_header(msg['Subject'])))
    body = msg.get_payload(decode=True).decode()
    assert '&lt;b&gt;froze&lt;/b&gt;' in body and '/write' in body


def test_rejects_empty_and_too_long():
    assert _send({'message': '   '})[0]['statusCode'] == 400
    assert _send({'message': 'x' * 2001})[0]['statusCode'] == 400
    assert _send('not json')[0]['statusCode'] == 400


def test_nothing_is_written_to_the_table():
    with mock.patch.object(app.user_service, 'get_single_user', return_value=_user()), \
         mock.patch.object(app, 'ses_client'), mock.patch('boto3.resource') as resource:
        app.lambda_handler(_event({'message': 'hi'}), None)
    resource.assert_not_called()


def test_learner_gets_a_confirmation_with_their_message():
    result, ses = _send({'message': 'Could quizzes have audio?'})
    kwargs = ses.send_raw_email.call_args_list[1].kwargs
    assert kwargs['Destinations'] == ['learner@example.com']
    msg = email.message_from_bytes(kwargs['RawMessage']['Data'])
    assert msg['Subject'] == 'We got your feedback'
    assert msg['Reply-To'] == 'nihao@haohaotiantian.com'
    body = msg.get_payload(decode=True).decode()
    assert 'Hi 小安,' in body and 'Could quizzes have audio?' in body


def test_a_failed_confirmation_still_reports_success():
    with mock.patch.object(app.user_service, 'get_single_user', return_value=_user()), \
         mock.patch.object(app, 'ses_client') as ses:
        ses.send_raw_email.side_effect = [{'MessageId': '1'}, Exception('SES down')]
        result = app.lambda_handler(_event({'message': 'hi'}), None)
    assert result['statusCode'] == 200
