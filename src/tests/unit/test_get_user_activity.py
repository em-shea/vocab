# Unit test for the 'get_user_activity' function
import json
import unittest
from datetime import datetime
from unittest import mock

from models import User, Subscription, Sentence, Word, Writing
from get_user_activity.app import lambda_handler


def _sentence(date_created, word_id="WORD#1"):
    return Sentence(
        sentence_id="s1",
        sentence="我说你好。",
        date_created=date_created,
        list_id="123",
        character_set="simplified",
        word=Word(
            word_id=word_id, simplified="你好", traditional="你好", pinyin="nǐ hǎo",
            definition="hello", audio_file_key="", difficulty_level="Beginner",
            hsk_level="1",
        ),
    )


def _user():
    return User(
        email_address="test@email.com",
        user_id="abc",
        character_set_preference="simplified",
        user_alias="Not set",
        user_alias_pinyin="Not set",
        user_alias_emoji="Not set",
        subscriptions=[
            Subscription(
                list_name="HSK Level 1",
                unique_list_id="123#SIMPLIFIED",
                list_id="123",
                character_set="simplified",
                status="subscribed",
                date_subscribed="2021-01-01T00:00:00",
            )
        ],
        quizzes=[],
        sentences=[],
    )


def _review_word(date_sent):
    return {
        "list_id": "123",
        "date_sent": date_sent,
        "word": {
            "word_id": "WORD#1",
            "simplified": "你好",
            "traditional": "你好",
            "pinyin": "nǐ hǎo",
            "definition": "hello",
            "audio_file_key": "",
            "difficulty_level": "Beginner",
            "hsk_level": "1",
        },
    }


class GetUserActivityTest(unittest.TestCase):

    @mock.patch('review_word_service.get_review_words')
    @mock.patch('user_service.get_single_user_with_activity')
    def test_build(self, get_user_mock, get_review_words_mock):
        today = datetime.today().strftime('%Y-%m-%d')
        get_user_mock.return_value = _user()
        get_review_words_mock.return_value = {"123": [_review_word(today)]}

        response = lambda_handler(self.apig_event(), "")
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(get_user_mock.call_count, 1)
        # One subscribed list -> one review-word query.
        self.assertEqual(get_review_words_mock.call_count, 1)

        # quizzes/sentences are replaced by a date-keyed "activity" map (10 days).
        self.assertNotIn("quizzes", body)
        self.assertNotIn("sentences", body)
        self.assertEqual(len(body["activity"]), 10)

        # Today's review word is bucketed under today's date.
        self.assertIn(today, body["activity"])
        todays_words = body["activity"][today]["review_words"]
        self.assertEqual(len(todays_words), 1)
        self.assertEqual(todays_words[0]["word"]["simplified"], "你好")

    @mock.patch('review_word_service.get_review_words')
    @mock.patch('user_service.get_single_user_with_activity')
    def test_matching_sentence_is_attached_to_its_review_word(self, get_user_mock, get_review_words_mock):
        # Regression: this assigned into user_activity[date]['review_words']['sentence']
        # where review_words is a list -> TypeError on any day a sentence matched a word.
        today = datetime.today().strftime('%Y-%m-%d')
        user = _user()
        user.sentences = [_sentence(today)]
        get_user_mock.return_value = user
        get_review_words_mock.return_value = {"123": [_review_word(today)]}

        response = lambda_handler(self.apig_event(), "")
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        todays_words = body["activity"][today]["review_words"]
        self.assertEqual(len(todays_words), 1)
        self.assertEqual(todays_words[0]["sentence"]["sentence"], "我说你好。")

    @mock.patch('review_word_service.get_review_words')
    @mock.patch('user_service.get_single_user_with_activity')
    def test_sentence_for_a_different_word_is_not_attached(self, get_user_mock, get_review_words_mock):
        today = datetime.today().strftime('%Y-%m-%d')
        user = _user()
        user.sentences = [_sentence(today, word_id="WORD#other")]
        get_user_mock.return_value = user
        get_review_words_mock.return_value = {"123": [_review_word(today)]}

        response = lambda_handler(self.apig_event(), "")
        body = json.loads(response["body"])

        todays_words = body["activity"][today]["review_words"]
        self.assertNotIn("sentence", todays_words[0])

    @mock.patch('review_word_service.get_review_words')
    @mock.patch('user_service.get_single_user_with_activity')
    def test_writing_practice_marks_its_word(self, get_user_mock, get_review_words_mock):
        today = datetime.today().strftime('%Y-%m-%d')
        user = _user()
        user.writings = [Writing(list_id="123", word_id="WORD#1", date_created=today)]
        get_user_mock.return_value = user
        get_review_words_mock.return_value = {"123": [_review_word(today)]}

        body = json.loads(lambda_handler(self.apig_event(), "")["body"])

        self.assertTrue(body["activity"][today]["review_words"][0]["written"])
        self.assertNotIn("writings", body)

    @mock.patch('review_word_service.get_review_words')
    @mock.patch('user_service.get_single_user_with_activity')
    def test_writing_for_another_word_list_or_day_does_not_count(self, get_user_mock, get_review_words_mock):
        today = datetime.today().strftime('%Y-%m-%d')
        user = _user()
        user.writings = [
            Writing(list_id="123", word_id="WORD#other", date_created=today),
            Writing(list_id="999", word_id="WORD#1", date_created=today),
            Writing(list_id="123", word_id="WORD#1", date_created="2000-01-01"),
        ]
        get_user_mock.return_value = user
        get_review_words_mock.return_value = {"123": [_review_word(today)]}

        body = json.loads(lambda_handler(self.apig_event(), "")["body"])

        self.assertFalse(body["activity"][today]["review_words"][0]["written"])

    def apig_event(self):
        return {
            "resource": "/user_activity",
            "path": "/user_activity",
            "httpMethod": "GET",
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "abc",
                        "email": "test@email.com",
                    }
                }
            },
            "body": None,
            "isBase64Encoded": False,
        }


if __name__ == '__main__':
    unittest.main()
