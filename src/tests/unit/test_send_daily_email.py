import os
import unittest
from unittest import mock

from models import User, Subscription
from send_daily_email.app import (
    lambda_handler, assemble_html_content, assemble_word_html_content, get_announcement,
)

LIST_ID = "1ebcad41-197a-6700-95a3-acde48001122"


def _subscription(status, list_id=LIST_ID, list_name="HSK Level 6"):
    return Subscription(
        list_name=list_name,
        unique_list_id=list_id + "#TRADITIONAL",
        list_id=list_id,
        character_set="traditional",
        status=status,
        date_subscribed="2021-06-16T23:06:48.646688",
    )


def _todays_word():
    return {
        "word": {
            "simplified": "前面", "traditional": "前面", "pinyin": "qián miàn",
            "definition": "in front", "audio_file_key": "", "difficulty_level": "Advanced",
            "hsk_level": "6",
        }
    }


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

    @mock.patch('send_daily_email.app.send_email')
    @mock.patch('send_daily_email.app.get_announcement', return_value=None)
    @mock.patch('user_service.get_all_users')
    @mock.patch('send_daily_email.app.get_daily_words')
    @mock.patch('send_daily_email.app.update_idempotency_table')
    @mock.patch('send_daily_email.app.check_idempotency_key', return_value=[])
    def test_one_user_with_a_wordless_list_does_not_stop_the_send(
        self, check_idem_mock, update_idem_mock, get_daily_words_mock,
        get_all_users_mock, get_announcement_mock, send_email_mock,
    ):
        # Only the HSK 6 list got a word today. The first user subscribes to a list
        # that has none - previously a KeyError raised outside the per-user try/except,
        # killing the send for everyone after them.
        get_daily_words_mock.return_value = {LIST_ID: [_todays_word()]}
        get_all_users_mock.return_value = [
            _user("wordless@test.com",
                  [_subscription("subscribed", list_id="no-word-today", list_name="My list")]),
            _user("fine@test.com", [_subscription("subscribed")]),
        ]

        lambda_handler(self.scheduled_event(), "")

        # The user behind the wordless list still gets their email.
        self.assertEqual(send_email_mock.call_count, 1)
        self.assertEqual(send_email_mock.call_args.args[0].email_address, "fine@test.com")


class AssembleEmailContentTest(unittest.TestCase):

    def test_subscription_with_no_word_today_is_omitted(self):
        content = assemble_word_html_content(
            "test@test.com", _subscription("subscribed", list_id="no-word-today"), {}
        )
        self.assertEqual(content, "")

    def test_subscription_with_an_empty_word_list_is_omitted(self):
        content = assemble_word_html_content(
            "test@test.com", _subscription("subscribed"), {LIST_ID: []}
        )
        self.assertEqual(content, "")

    def test_returns_none_when_no_subscribed_list_has_a_word(self):
        user = _user("test@test.com", [_subscription("subscribed")])

        # No email is better than an email with an empty word slot.
        self.assertIsNone(assemble_html_content(user, {}, None))

    def test_renders_the_word_when_one_is_set(self):
        user = _user("test@test.com", [_subscription("subscribed")])

        content = assemble_html_content(user, {LIST_ID: [_todays_word()]}, None)

        self.assertIn("前面", content)
        self.assertIn("qián miàn", content)
        # Announcement slot is emptied rather than left as a placeholder.
        self.assertNotIn("{announcement_slot}", content)


class GetAnnouncementTest(unittest.TestCase):

    def _s3_body(self, payload):
        return {"Body": mock.Mock(read=mock.Mock(return_value=payload.encode("utf-8")))}

    @mock.patch('boto3.client')
    def test_renders_the_packaged_announcements_template(self, boto_client_mock):
        boto_client_mock.return_value.get_object.return_value = self._s3_body(
            '{"message": "Site maintenance Friday"}'
        )

        announcement = get_announcement()

        # Regression: this used to open a nonexistent 'announcements_template.html'
        # and raise before any email was sent.
        self.assertIsNotNone(announcement)
        self.assertIn("Site maintenance Friday", announcement)

    @mock.patch('boto3.client')
    def test_returns_none_when_no_announcement_file_exists(self, boto_client_mock):
        boto_client_mock.return_value.get_object.side_effect = Exception("NoSuchKey")

        self.assertIsNone(get_announcement())

    @mock.patch('boto3.client')
    def test_malformed_announcement_degrades_to_none(self, boto_client_mock):
        boto_client_mock.return_value.get_object.return_value = self._s3_body("not json")

        # A bad announcement file must not take down the day's send.
        self.assertIsNone(get_announcement())


if __name__ == '__main__':
    unittest.main()
