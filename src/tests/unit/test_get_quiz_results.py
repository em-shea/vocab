import json
import unittest
from unittest import mock

from get_quiz_results.app import lambda_handler


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
