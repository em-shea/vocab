import json
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone

from set_writing.app import lambda_handler, writing_date, save_writing, MAX_DAYS_BACK


def event(body, sub="user-1"):
    return {
        "body": json.dumps(body) if not isinstance(body, str) else body,
        "requestContext": {"authorizer": {"claims": {"sub": sub}}},
    }


BODY = {"list_id": "L1", "word_id": "W1", "characters": "爱护", "character_set": "simplified"}


class SetWritingTest(unittest.TestCase):

    @mock.patch('set_writing.app.save_writing')
    def test_records_practice_under_the_words_date(self, save_mock):
        word_date = (datetime.now(timezone.utc).date() - timedelta(days=2)).isoformat()
        response = lambda_handler(event({**BODY, "date": word_date}), "")
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"])["data"]["date"], word_date)
        self.assertEqual(save_mock.call_args.args[0], "user-1")
        self.assertEqual(save_mock.call_args.args[2], word_date)

    @mock.patch('set_writing.app.save_writing')
    def test_missing_fields_or_bad_dates_are_400_and_save_nothing(self, save_mock):
        for body in ({"list_id": "L1"}, {**BODY, "date": "21/11/2026"}, {**BODY, "date": "2999-01-01"}, "not json"):
            self.assertEqual(lambda_handler(event(body), "")["statusCode"], 400, body)
        save_mock.assert_not_called()

    @mock.patch('set_writing.app.save_writing', side_effect=Exception("dynamo down"))
    def test_a_failed_save_is_502(self, save_mock):
        self.assertEqual(lambda_handler(event(BODY), "")["statusCode"], 502)

    def test_writing_date(self):
        today = datetime(2026, 11, 23).date()
        self.assertEqual(writing_date(None, today), "2026-11-23")
        self.assertEqual(writing_date("2026-11-20", today), "2026-11-20")
        with self.assertRaises(ValueError):
            writing_date((today - timedelta(days=MAX_DAYS_BACK + 1)).isoformat(), today)

    @mock.patch('set_writing.app.table')
    def test_one_item_per_user_day_list_and_word(self, table_mock):
        save_writing("user-1", BODY, "2026-11-23")
        item = table_mock.put_item.call_args.kwargs["Item"]
        self.assertEqual(item["PK"], "USER#user-1")
        self.assertEqual(item["SK"], "DATE#2026-11-23#WRITING#L1#W1")
        self.assertEqual(item["Characters"], "爱护")
        # Only put_item: nothing is read, updated or deleted.
        self.assertEqual([c[0] for c in table_mock.method_calls], ["put_item"])
