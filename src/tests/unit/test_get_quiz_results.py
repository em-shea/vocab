import json
import unittest
from datetime import datetime, timedelta
from unittest import mock

import quiz_results_service
from get_quiz_results.app import lambda_handler
from set_quiz_results.app import put_quiz_result


def _quiz_body(quiz_id="q1", correct=8):
    return {
        "quiz_id": quiz_id,
        "quiz_data": [],
        "list_id": "123",
        "character_set": "simplified",
        "question_quantity": 10,
        "correct_answers": correct,
    }


def test_quizzes_written_by_set_quiz_results_are_readable(dynamodb_table):
    """Round-trip regression: the read path must match the write path's key shape.

    retrieve_quiz_results queried SK begins_with('QUIZ#') while set_quiz_results
    writes 'DATE#<date>#QUIZ#<id>', so this always came back empty - and the
    progression layer is meant to build on this history.
    """
    today = datetime.today().strftime('%Y-%m-%d')
    put_quiz_result("user-1", _quiz_body(), today)

    results = quiz_results_service.retrieve_quiz_results("user-1", 7)

    assert len(results) == 1
    assert results[0]["quiz_id"] == "q1"
    assert results[0]["correct_answers"] == 8


def test_quiz_taken_today_is_inside_the_range(dynamodb_table):
    """The old filter compared '%Y-%m-%d' against an isoformat string, excluding
    the boundary day."""
    today = datetime.today().strftime('%Y-%m-%d')
    put_quiz_result("user-1", _quiz_body(), today)

    # A one-day range must still include today's quiz.
    assert len(quiz_results_service.retrieve_quiz_results("user-1", 1)) == 1


def test_quizzes_outside_the_range_are_excluded(dynamodb_table):
    old_date = (datetime.today() - timedelta(days=40)).strftime('%Y-%m-%d')
    recent_date = (datetime.today() - timedelta(days=2)).strftime('%Y-%m-%d')
    put_quiz_result("user-1", _quiz_body(quiz_id="old"), old_date)
    put_quiz_result("user-1", _quiz_body(quiz_id="recent"), recent_date)

    results = quiz_results_service.retrieve_quiz_results("user-1", 7)

    assert [r["quiz_id"] for r in results] == ["recent"]


def test_sentences_are_filtered_out_of_the_quiz_query(dynamodb_table):
    today = datetime.today().strftime('%Y-%m-%d')
    put_quiz_result("user-1", _quiz_body(), today)
    dynamodb_table.put_item(Item={
        "PK": "USER#user-1",
        "SK": f"DATE#{today}#SENTENCE#s1",
        "Sentence id": "s1",
    })

    results = quiz_results_service.retrieve_quiz_results("user-1", 7)

    assert len(results) == 1
    assert results[0]["quiz_id"] == "q1"


def _event(body):
    return {
        "resource": "/quizzes",
        "httpMethod": "GET",
        "requestContext": {"authorizer": {"claims": {"sub": "user-123"}}},
        "body": body,
    }


QUIZ_RESULTS = [{"quiz_id": "q1", "correct_answers": 8}]


class GetQuizResultsTest(unittest.TestCase):

    @mock.patch('quiz_results_service.retrieve_quiz_results', return_value=QUIZ_RESULTS)
    def test_defaults_to_seven_days_when_no_body(self, retrieve_mock):
        response = lambda_handler(_event(None), "")
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        retrieve_mock.assert_called_once_with("user-123", 7)
        self.assertEqual(body["data"], QUIZ_RESULTS)

    @mock.patch('quiz_results_service.retrieve_quiz_results', return_value=QUIZ_RESULTS)
    def test_honours_thirty_day_range(self, retrieve_mock):
        lambda_handler(_event(json.dumps({"date_range": 30})), "")
        retrieve_mock.assert_called_once_with("user-123", 30)

    @mock.patch('quiz_results_service.retrieve_quiz_results', return_value=QUIZ_RESULTS)
    def test_invalid_range_falls_back_to_seven_days(self, retrieve_mock):
        lambda_handler(_event(json.dumps({"date_range": 99})), "")
        retrieve_mock.assert_called_once_with("user-123", 7)

    @mock.patch('quiz_results_service.retrieve_quiz_results', side_effect=Exception("dynamo down"))
    def test_retrieve_failure_returns_502(self, retrieve_mock):
        response = lambda_handler(_event(None), "")
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 502)
        self.assertFalse(body["success"])


if __name__ == '__main__':
    unittest.main()
