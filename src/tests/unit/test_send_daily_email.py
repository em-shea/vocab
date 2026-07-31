import unittest
from unittest import mock

from models import User, Subscription
from send_daily_email.app import lambda_handler


def _subscription(status):
    return Subscription(
        list_name="HSK Level 6",
        unique_list_id="1ebcad41-197a-6700-95a3-acde48001122#TRADITIONAL",
        list_id="1ebcad41-197a-6700-95a3-acde48001122",
        character_set="traditional",
        status=status,
        date_subscribed="2021-06-16T23:06:48.646688",
    )


def _user(email, subscriptions):
    return User(
        email_address=email,
        user_id=email,
        character_set_preference="traditional",
        user_alias="Not set",
        user_alias_pinyin="Not set",
        user_alias_emoji="Not set",
        subscriptions=subscriptions,
        quizzes=[],
        sentences=[],
    )


class SendDailyEmailTest(unittest.TestCase):

    def scheduled_event(self):
        return {
            "time": "2021-01-01T20:00:00Z",
            "detail": {"idempotency-key": "2021-01-01-daily-email"},
        }

    @mock.patch('send_daily_email.app.send_email')
    @mock.patch('send_daily_email.app.assemble_html_content', return_value="<html></html>")
    @mock.patch('send_daily_email.app.get_announcement', return_value=None)
    @mock.patch('user_service.get_all_users')
    @mock.patch('send_daily_email.app.get_daily_words', return_value={})
    @mock.patch('send_daily_email.app.update_idempotency_table')
    @mock.patch('send_daily_email.app.check_idempotency_key', return_value=[])
    def test_sends_one_email_per_subscribed_user(
        self, check_idem_mock, update_idem_mock, get_daily_words_mock,
        get_all_users_mock, get_announcement_mock, assemble_mock, send_email_mock,
    ):
        # One subscribed user, one user with no active subscription.
        get_all_users_mock.return_value = [
            _user("subscribed@test.com", [_subscription("subscribed")]),
            _user("lapsed@test.com", [_subscription("unsubscribed")]),
        ]

        lambda_handler(self.scheduled_event(), "")

        # New idempotency key -> claim it, fetch words, and email only the subscribed user.
        self.assertEqual(check_idem_mock.call_count, 1)
        self.assertEqual(update_idem_mock.call_count, 1)
        self.assertEqual(get_all_users_mock.call_count, 1)
        self.assertEqual(send_email_mock.call_count, 1)
        emailed_user = send_email_mock.call_args.args[0]
        self.assertEqual(emailed_user.email_address, "subscribed@test.com")

    @mock.patch('send_daily_email.app.send_email')
    @mock.patch('user_service.get_all_users')
    @mock.patch('send_daily_email.app.update_idempotency_table')
    @mock.patch('send_daily_email.app.check_idempotency_key',
                return_value=[{"IdempotencyKey": "2021-01-01-daily-email"}])
    def test_skips_when_idempotency_key_already_exists(
        self, check_idem_mock, update_idem_mock, get_all_users_mock, send_email_mock,
    ):
        lambda_handler(self.scheduled_event(), "")

        # Key already processed -> no duplicate send, no user fetch, no re-claim.
        self.assertEqual(check_idem_mock.call_count, 1)
        self.assertEqual(update_idem_mock.call_count, 0)
        self.assertEqual(get_all_users_mock.call_count, 0)
        self.assertEqual(send_email_mock.call_count, 0)


if __name__ == '__main__':
    unittest.main()
